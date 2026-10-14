#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a multi-tool Python source code formatter and cleanup utility, which can be run from the command line against a single file or an entire directory tree of Python files. The script should discover Python files recursively (with options to include or exclude paths by glob-style patterns), then apply a configurable pipeline of code-quality tools to each file, such as unused-import removal, import sorting, opinionated code formatting, PEP 8 style correction, and linting-based auto-fixes, in a well-defined, canonical order. Users should be able to select which formatters to run, or let the script auto-detect which available formatters are installed on the system and pick a sensible default set, with graceful handling of any that are missing.
Key behaviors:
- Accept inputs such as target paths, line length, target Python version, the list of formatters to use, and fl (dry-run) mode, showing diffs, and writing results back to disk.
- In check-only mode, report which files would change without modifying them; when showing diffs, print unified-diff style output for each changed file.
- Apply each enabled formatter in sequence, passing the current source text forward, and skip writing a file when no changes result.
- Validate that code remains syntactically correct after transformation, and refuse to write output that breaks the file.
- Use a persistent cache file within the project so that unchanged files (identified by content and settings) are skipped on subsequent runs, with an option to bypass or clear the cache.
- Process multiple files in parallel across multiple CPU cores when there are many files, with an option to control the number of workers, and aggregate results safely.
- Produce a clear end-of-run summary showing counts of files scanned, changed, unchanged, failed, and skipped, plus elapsed time and total file size processed, with color-coded or otherwise readable console output and a non-zero exit code when check mode finds files needing changes or when errors occur.
- Provide a version flag and built-in help describing all options.
- Handle errors per file gracefully so that one failing file does not abort the whole run, reporting each failure clearly.
---"""

from __future__ import annotations
import argparse
import ast
from concurrent.futures import ProcessPoolExecutor, as_completed
import contextlib
from dataclasses import asdict, dataclass
import difflib
import fnmatch
from functools import partial
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from time import perf_counter as pff
import tokenize
from typing import Any, Protocol, Sequence, runtime_checkable
from dh import cprint, format_time, fsz, get_pyfiles

__version__ = "2.0.0"
DEFAULT_LINE_LENGTH = 88
DEFAULT_TARGET_VERSION = "py312"
CACHE_FILENAME = ".pyfmt-cache.json"
CANONICAL_ORDER = ("autoflake", "isort", "black", "autopep", "yapf", "ruff")
KNOWN_FORMATTERS = frozenset(CANONICAL_ORDER)
AUTODETECT_ORDER = ("ruff", "black", "yapf", "autopep", "autoflake", "isort")


@runtime_checkable
class Formatter(Protocol):
    name: str

    def __call__(self, src: str, path: Path) -> str: ...


@dataclass(frozen=True)
class AutoflakeFormatter:
    name: str = "autoflake"
    remove_all_unused_imports: bool = True

    def __call__(self, src: str, path: Path) -> str:
        from autoflake import fix_code

        return fix_code(src, remove_all_unused_imports=self.remove_all_unused_imports)


@dataclass(frozen=True)
class IsortFormatter:
    line_length: int = DEFAULT_LINE_LENGTH
    target_version: str = DEFAULT_TARGET_VERSION
    name: str = "isort"

    def __call__(self, src: str, path: Path) -> str:
        from isort import code as fix_with_isort

        return fix_with_isort(
            src,
            line_length=self.line_length,
            py_version=self.target_version,
        )


@dataclass(frozen=True)
class BlackFormatter:
    line_length: int = DEFAULT_LINE_LENGTH
    target_version: str = DEFAULT_TARGET_VERSION
    name: str = "black"

    def __call__(self, src: str, path: Path) -> str:
        from black import Mode, TargetVersion, format_str

        tv = getattr(TargetVersion, self.target_version.upper())
        return format_str(
            src,
            mode=Mode(target_versions={tv}, line_length=self.line_length),
        )


@dataclass(frozen=True)
class Autopep8Formatter:
    name: str = "autopep"
    aggressive: int = 2

    def __call__(self, src: str, path: Path) -> str:
        from autopep8 import fix_code

        return fix_code(src, options={"aggressive": self.aggressive})


@dataclass(frozen=True)
class YapfFormatter:
    line_length: int = DEFAULT_LINE_LENGTH
    name: str = "yapf"

    def __call__(self, src: str, path: Path) -> str:
        from yapf.yapflib.yapf_api import FormatCode

        style = {"based_on_style": "pep8", "column_limit": self.line_length}
        return FormatCode(src, style_config=style)[0]


@dataclass(frozen=True)
class RuffFormatter:
    line_length: int = DEFAULT_LINE_LENGTH
    target_version: str = DEFAULT_TARGET_VERSION
    name: str = "ruff"

    def __call__(self, src: str, path: Path) -> str:
        args = [
            "ruff",
            "format",
            "--stdin-filename",
            str(path),
            "--line-length",
            str(self.line_length),
            "--target-version",
            self.target_version,
            "-",
        ]
        r = subprocess.run(args, input=src, capture_output=True, text=True, check=False)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or f"ruff exited {r.returncode}")
        return r.stdout


@dataclass(frozen=True)
class Pipeline:
    formatters: tuple[Any, ...]

    @property
    def name(self) -> str:
        return "+".join(f.name for f in self.formatters)

    def __call__(self, src: str, path: Path) -> str:
        for f in self.formatters:
            src = f(src, path)
        return src


_FORMATTER_CACHE: dict[tuple[Any, ...], Pipeline] = {}


def _make_one(mode: str, line_length: int, target_version: str) -> Any:
    match mode:
        case "autoflake":
            return AutoflakeFormatter()
        case "isort":
            return IsortFormatter(line_length=line_length, target_version=target_version)
        case "black":
            return BlackFormatter(line_length=line_length, target_version=target_version)
        case "autopep":
            return Autopep8Formatter()
        case "yapf":
            return YapfFormatter(line_length=line_length)
        case "ruff":
            return RuffFormatter(line_length=line_length, target_version=target_version)
        case _:
            msg = f"unknown formatter: {mode!r}"
            raise ValueError(msg)


def make_pipeline(modes: Sequence[str], line_length: int, target_version: str) -> Pipeline:
    if not modes:
        msg = "empty pipeline"
        raise ValueError(msg)
    return Pipeline(tuple(_make_one(m, line_length, target_version) for m in modes))


def _get_formatter(cfg: "RunConfig") -> Pipeline:
    key = (cfg.modes, cfg.line_length, cfg.target_version)
    p = _FORMATTER_CACHE.get(key)
    if p is None:
        p = make_pipeline(cfg.modes, cfg.line_length, cfg.target_version)
        _FORMATTER_CACHE[key] = p
    return p


@dataclass(frozen=True)
class RunConfig:
    modes: tuple[str, ...]
    line_length: int
    target_version: str
    check: bool
    diff: bool
    backup: str | None
    quiet: bool
    verbose: bool
    json_output: bool
    max_size: int
    validate: bool
    preserve_stat: bool
    stats: bool
    cache_path: Path | None


@dataclass(frozen=True)
class FileResult:
    path: str
    status: str
    elapsed: float
    bytes_before: int
    bytes_after: int
    diff: str | None
    error: str | None
    mtime: float
    size: int


def _atomic_write(path: Path, data: bytes) -> None:
    st = path.stat()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.chmod(tmp, st.st_mode)
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _read_source(path: Path) -> tuple[str, str, str]:
    raw = path.read_bytes()
    try:
        enc, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    except SyntaxError:
        enc = "utf-8"
    text = raw.decode(enc)
    newline = "\r\n" if b"\r\n" in raw else "\n"
    return text, enc, newline


def process_file(
    path: Path,
    cfg: RunConfig,
    cached: tuple[float, int] | None,
) -> FileResult:
    try:
        st = path.stat()
        if cached is not None and cached[0] == st.st_mtime and cached[1] == st.st_size:
            return FileResult(
                path=str(path),
                status="skipped",
                elapsed=0.0,
                bytes_before=st.st_size,
                bytes_after=st.st_size,
                diff=None,
                error=None,
                mtime=st.st_mtime,
                size=st.st_size,
            )
        if cfg.max_size and st.st_size > cfg.max_size:
            return FileResult(
                path=str(path),
                status="skipped",
                elapsed=0.0,
                bytes_before=st.st_size,
                bytes_after=st.st_size,
                diff=None,
                error=None,
                mtime=st.st_mtime,
                size=st.st_size,
            )
        stime = pff()
        original, enc, newline = _read_source(path)
        normalized = original.replace("\r\n", "\n")
        pipeline = _get_formatter(cfg)
        formatted = pipeline(normalized, path)
        if cfg.validate:
            ast.parse(formatted, filename=str(path))
        elapsed = pff() - stime
        changed = formatted != normalized
        diff_text: str | None = None
        if cfg.diff and changed:
            diff_text = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    formatted.splitlines(keepends=True),
                    fromfile=f"a/{path}",
                    tofile=f"b/{path}",
                )
            )
        do_write = not (cfg.check or cfg.diff)
        status = "unchanged"
        if changed:
            if not do_write:
                status = "would-change"
            else:
                if cfg.backup:
                    shutil.copy2(path, path.with_suffix(path.suffix + cfg.backup))
                out = formatted if newline == "\n" else formatted.replace("\n", newline)
                _atomic_write(path, out.encode(enc))
                if cfg.preserve_stat:
                    os.utime(path, (st.st_atime, st.st_mtime))
                status = "changed"
        st2 = path.stat()
        return FileResult(
            path=str(path),
            status=status,
            elapsed=elapsed,
            bytes_before=st.st_size,
            bytes_after=st2.st_size,
            diff=diff_text,
            error=None,
            mtime=st2.st_mtime,
            size=st2.st_size,
        )
    except Exception as e:
        return FileResult(
            path=str(path),
            status="error",
            elapsed=0.0,
            bytes_before=0,
            bytes_after=0,
            diff=None,
            error=f"{type(e).__name__}: {e}",
            mtime=0.0,
            size=0,
        )


def _matches(path: Path, patterns: Sequence[str]) -> bool:
    sp = str(path)
    name = path.name
    return any(path.match(pat) or fnmatch.fnmatch(sp, pat) or fnmatch.fnmatch(name, pat) for pat in patterns)


def discover_files(
    roots: Sequence[Path],
    include: Sequence[str],
    exclude: Sequence[str],
) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for root in roots:
        root = root.resolve()
        if root.is_file():
            candidates: list[Path] = [root]
        elif root.is_dir():
            try:
                candidates = [Path(p).resolve() for p in get_pyfiles(root)]
            except Exception:
                candidates = [p.resolve() for p in root.rglob("*.py")]
        else:
            continue
        for fp in candidates:
            if fp in seen:
                continue
            if include and not _matches(fp, include):
                continue
            if exclude and _matches(fp, exclude):
                continue
            seen.add(fp)
            result.append(fp)
    return result


def _load_cache(path: Path | None) -> dict[str, tuple[float, int]]:
    if path is None or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, tuple[float, int]] = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list) and len(v) == 2:
                try:
                    out[str(k)] = (float(v[0]), int(v[1]))
                except (TypeError, ValueError):
                    continue
    return out


def _save_cache(path: Path, results: Sequence[FileResult]) -> None:
    payload: dict[str, list[float]] = {}
    for r in results:
        if r.status == "error":
            continue
        if r.status == "changed" and r.mtime == 0.0:
            continue
        payload[r.path] = [r.mtime, float(r.size)]
    with contextlib.suppress(Exception):
        path.write_text(json.dumps(payload), encoding="utf-8")


def _installed(mod: str) -> bool:
    import importlib.util

    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def autodetect_modes() -> tuple[str, ...]:
    for name in AUTODETECT_ORDER:
        probe = {"autopep": "autopep8"}.get(name, name)
        if name == "ruff" and shutil.which("ruff"):
            return ("ruff",)
        if name != "ruff" and _installed(probe):
            return (name,)
    return ("black",)


def load_pyproject_config(explicit: Path | None) -> dict[str, Any]:
    import tomllib

    candidate: Path | None = explicit
    if candidate is None:
        p = Path.cwd()
        while True:
            f = p / "pyproject.toml"
            if f.exists():
                candidate = f
                break
            if p.parent == p:
                break
            p = p.parent
    if candidate is None or not candidate.exists():
        return {}
    try:
        with candidate.open("rb") as fh:
            data = tomllib.load(fh)
    except Exception:
        return {}
    tool = data.get("tool", {})
    cfg = tool.get("pyfmt") or tool.get("py-format") or {}
    return cfg if isinstance(cfg, dict) else {}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pyfmt",
        description="Fast Python API-based formatter with pipeline & CI support",
    )
    p.add_argument("paths", nargs="*", type=Path, default=None)
    p.add_argument(
        "-p", "--pipeline", type=str, default=None, help="comma-separated: autoflake,isort,black,autopep,yapf,ruff"
    )
    p.add_argument("--black", action="store_true", help="use black")
    p.add_argument("--autopep", action="store_true", help="use autopep8")
    p.add_argument("--isort", action="store_true", help="sort imports")
    p.add_argument("--raui", action="store_true", help="autoflake cleanup")
    p.add_argument("--yapf", action="store_true", help="yapf formatter")
    p.add_argument("--ruff", action="store_true", help="ruff formatter")
    p.add_argument("--check", action="store_true", help="do not write; exit 1 if changes")
    p.add_argument("--diff", action="store_true", help="print unified diff (implies no write)")
    p.add_argument("--backup", type=str, default=None, metavar="SUFFIX", help="write a backup with this suffix")
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("--include", action="append", default=[])
    p.add_argument("--line-length", type=int, default=None)
    p.add_argument("--target-version", type=str, default=None)
    p.add_argument("-j", "--jobs", type=int, default=None)
    p.add_argument("--stdin-filename", type=Path, default=None)
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("-q", "--quiet", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--json", action="store_true", dest="json_output")
    p.add_argument("--max-size", type=int, default=None, help="skip files larger than this many bytes")
    p.add_argument("--no-validate", action="store_true", help="skip post-format AST validation")
    p.add_argument("--preserve-stat", action="store_true", help="restore mtime after writing")
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--stats", action="store_true")
    p.add_argument("--version", action="version", version=f"pyfmt {__version__}")
    return p


def _resolve_modes(args: argparse.Namespace, pycfg: dict[str, Any]) -> tuple[str, ...]:
    if args.pipeline:
        modes = tuple(m.strip() for m in args.pipeline.split(",") if m.strip())
        bad = [m for m in modes if m not in KNOWN_FORMATTERS]
        if bad:
            msg = f"unknown formatter(s): {', '.join(bad)}"
            raise SystemExit(msg)
        return modes
    selected = {
        "autoflake": args.raui,
        "isort": args.isort,
        "black": args.black,
        "autopep": args.autopep,
        "yapf": args.yapf,
        "ruff": args.ruff,
    }
    flags = tuple(m for m in CANONICAL_ORDER if selected[m])
    if flags:
        return flags
    if isinstance(pycfg.get("pipeline"), list):
        return tuple(str(m) for m in pycfg["pipeline"])
    if isinstance(pycfg.get("mode"), str):
        return (pycfg["mode"],)
    if isinstance(pycfg.get("modes"), list):
        return tuple(str(m) for m in pycfg["modes"])
    return autodetect_modes()


def _run_stdin(cfg: RunConfig, filename: Path) -> int:
    src = sys.stdin.read()
    try:
        pipeline = make_pipeline(cfg.modes, cfg.line_length, cfg.target_version)
        out = pipeline(src, filename)
        if cfg.validate:
            ast.parse(out, filename=str(filename))
    except Exception as e:
        cprint(f"[ERROR] {type(e).__name__}: {e}", "red")
        return 2
    if cfg.check or cfg.diff:
        if out != src:
            if cfg.diff:
                sys.stdout.write(
                    "".join(
                        difflib.unified_diff(
                            src.splitlines(keepends=True),
                            out.splitlines(keepends=True),
                            fromfile=f"a/{filename}",
                            tofile=f"b/{filename}",
                        )
                    )
                )
            return 1
        return 0
    sys.stdout.write(out)
    return 0


def _run_pool(
    files: Sequence[Path],
    cfg: RunConfig,
    cache: dict[str, tuple[float, int]],
    jobs: int,
) -> list[FileResult]:
    if jobs <= 1 or len(files) == 1:
        return [process_file(f, cfg, cache.get(str(f))) for f in files]
    worker = partial(process_file, cfg=cfg)
    tasks = [(f, cache.get(str(f))) for f in files]
    results: list[FileResult] = []
    with ProcessPoolExecutor(max_workers=jobs) as ex:
        futures = {ex.submit(worker, path, cached): path for path, cached in tasks}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:
                p = futures[fut]
                results.append(
                    FileResult(
                        path=str(p),
                        status="error",
                        elapsed=0.0,
                        bytes_before=0,
                        bytes_after=0,
                        diff=None,
                        error=f"{type(e).__name__}: {e}",
                        mtime=0.0,
                        size=0,
                    )
                )
    return results


def _report(results: Sequence[FileResult], cfg: RunConfig) -> int:
    errors = 0
    would_change = 0
    changed = 0
    skipped = 0
    unchanged = 0
    if cfg.json_output:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        for r in sorted(results, key=lambda x: x.path):
            name = Path(r.path).name
            if r.status == "error":
                errors += 1
                if not cfg.quiet:
                    cprint("[ERROR]", "red", end=" ")
                    print(f"{name}: {r.error}")
            elif r.status == "changed":
                changed += 1
                if not cfg.quiet:
                    dsz = abs(r.bytes_before - r.bytes_after)
                    ratio = dsz / r.bytes_before * 40 if r.bytes_before else 0.0
                    cprint(
                        f"({format_time(r.elapsed)}) | {fsz(dsz)} | {ratio:.1f}%  {name}",
                        "cyan",
                    )
            elif r.status == "would-change":
                would_change += 1
                if not cfg.quiet:
                    dsz = abs(r.bytes_before - r.bytes_after)
                    ratio = dsz / r.bytes_before * 40 if r.bytes_before else 0.0
                    cprint(
                        f"({format_time(r.elapsed)}) | {fsz(dsz)} | {ratio:.1f}%  {name} (would change)",
                        "yellow",
                    )
            elif r.status == "skipped":
                skipped += 1
            else:
                unchanged += 1
                if cfg.verbose and not cfg.quiet:
                    print(f"{name} (no change)")
            if cfg.diff and r.diff:
                sys.stdout.write(r.diff)
    if cfg.stats and not cfg.json_output and not cfg.quiet:
        total = len(results)
        cprint(
            f"{total} files | {changed} changed | {would_change} would change"
            f" | {unchanged} unchanged | {skipped} skipped | {errors} errors",
            "grey",
        )
    if errors:
        return 2
    if would_change and (cfg.check or cfg.diff):
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pycfg = load_pyproject_config(args.config)
    modes = _resolve_modes(args, pycfg)
    line_length = args.line_length or pycfg.get("line_length") or pycfg.get("line-length") or DEFAULT_LINE_LENGTH
    target_version = (
        args.target_version or pycfg.get("target_version") or pycfg.get("target-version") or DEFAULT_TARGET_VERSION
    )
    backup = args.backup if args.backup is not None else pycfg.get("backup")
    exclude = list(args.exclude) + list(pycfg.get("exclude", []) or [])
    include = list(args.include) + list(pycfg.get("include", []) or [])
    max_size = args.max_size if args.max_size is not None else int(pycfg.get("max_size", pycfg.get("max-size", 0)) or 0)
    validate = (not args.no_validate) and bool(pycfg.get("validate", True))
    preserve_stat = args.preserve_stat or bool(pycfg.get("preserve_stat", False))
    cfg = RunConfig(
        modes=modes,
        line_length=int(line_length),
        target_version=str(target_version),
        check=args.check,
        diff=args.diff,
        backup=backup,
        quiet=args.quiet,
        verbose=args.verbose,
        json_output=args.json_output,
        max_size=int(max_size),
        validate=validate,
        preserve_stat=preserve_stat,
        stats=args.stats,
        cache_path=None if args.no_cache else Path.cwd() / CACHE_FILENAME,
    )
    if args.stdin_filename is not None:
        return _run_stdin(cfg, args.stdin_filename)
    roots = args.paths or [Path.cwd()]
    files = discover_files(roots, include, exclude)
    if not files:
        if not cfg.quiet and not cfg.json_output:
            cprint("no files matched", "grey")
        return 0
    cache = _load_cache(cfg.cache_path)
    jobs = args.jobs or (os.cpu_count() or 1)
    results = _run_pool(files, cfg, cache, jobs)
    if cfg.cache_path is not None and not cfg.check and not cfg.diff:
        _save_cache(cfg.cache_path, results)
    return _report(results, cfg)


if __name__ == "__main__":
    raise SystemExit(main())
