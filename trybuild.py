#!/data/data/com.termux/files/usr/bin/env python
"""Create a Python 3 command-line automation script (intended to run under Termux on Android, shebang `/data/data/com.termux/files/usr/bin/python3.12`) named `build_all.py` whose purpose is to discover and build every Python packaging project found under the current working directory, in parallel, and report which ones succeeded, failed, or were skipped.

Functional requirements:

1. **Project discovery**
   - Recursively walk the current directory.
   - A "project" is any directory that contains a `setup.py` and/or a `pyproject.toml`.
   - While walking, prune (do not descend into) junk directories so they are never scanned: virtual environments, version-control directories (e.g. `.git`), cache directories, `build`/`dist` directories, `node_modules`, and `*.egg-info` directories.
   - For directories that only have a `pyproject.toml`: parse the TOML. If it contains neither a `[project]` table nor a `[build-system]` table (i.e., it only has tool-specific config like `[tool.ruff]`) and there is no `setup.py` present, treat this as a non-buildable project and report it as **SKIPPED** rather than attempting a build or counting it as a failure.
   - If the TOML is invalid/unparseable, do NOT skip it — still attempt the build so the real error from the build tool is surfaced to the user.

2. **Building**
   - Use the `build` package (`python -m build`) to build each discovered project in a subprocess.
   - Support an `--out DIR` option: when provided, keep the resulting build artifacts, placing each project's output in a subdirectory of `DIR` named after the project's relative path with path separators replaced by `__` (so art When not provided, build into a temporary directory that is discarded afterward.
   - Support a `--no-isolation` flag: when set, pass the equivalent "no build isolation" option to `build` so it uses the current Python environment and does not try to download build dependencies from the network.
   - Run builds with a reasonable timeout; each build should run in its own process session/group so that on timeout the entire process tree (pip, build backends, etc.) can be killed, not just the top-level process.
   - Note (document only, not something to "fix"): a `setup.py`-based build may create a `*.egg-info` directory inside the source folder as a side effect of setuptools; this is expected setuptools behavior.

3. **Concurrency**
   - Build exactly 4 projects at a time using a multiprocessing pool (`multiprocessing.Pool(4)` with `imap_unordered`).
   - Worker processes must only perform the build and return a structured result object (e.g., project path, status, duration, captured output/error) — workers must NOT perform any logging themselves, to avoid logging-handler issues under the "spawn" multiprocessing start method on Windows/macOS.
   - The parent/main process receives results from the pool and performs all logging/reporting using `loguru`.

4. **CLI usage**
   - `python build_all.py` — build everything found, discarding artifacts afterward.
   - `python build_all.py --out dist_all` — build everything, keeping artifacts under `dist_all/`.
   - `python build_all.py --no-isolation` — build using the current environment without isolation/network access for build dependencies.
   - Use `argparse` for argument parsing.

5. **Output / reporting**
   - Use `loguru` for all progress and result logging (per-project start/success/failure/skip messages and a final summary of how many projects were built, skipped, and failed).
   - Handle `Ctrl-C` (KeyboardInterrupt) gracefully, terminating the pool/workers cleanly.

6. **Exit codes**
   - `0` — everything built successfully or was legitimately skipped.
   - `1` — one or more builds failed, or a setup/discovery error occurred.
   - `130` — interrupted by Ctrl-C.

7. **Dependencies**
   - Requires the `build` and `loguru` Python packages (document this, e.g. `pip install build loguru`).
   - Likely needed standard-library modules: `argparse`, `contextlib`, `functools`, `importlib.util`, `multiprocessing`, `os`/`pathlib`, `shutil`, `subprocess`, `sys`, `tempfile`, `time`, and a TOML parser (e.g. `tomllib`/`tomli`).

Include a module-level docstring/header comment summarizing the script's purpose, usage examples, and the design notes above (project detection rules, pruning rules, skip-vs-fail logic for `pyproject.toml`, the 4-worker no-logging-in-workers design, per-build process-group timeout handling, and the egg-info side effect note), matching the style of inline documentation at the top of the file.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/RU4EaLnuGkVoAwKQYjAXcN"""

import argparse
import contextlib
import functools
import importlib.util
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from loguru import logger

try:
    import tomllib
except ImportError:
    tomllib = None
WORKERS = 4
MARKERS = ("setup.py", "pyproject.toml")
SKIP_DIRS = frozenset({
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    ".tox",
    ".nox",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    ".eggs",
    "site-packages",
})
TAIL_LINES = 40


@dataclass(frozen=True, slots=True)
class Result:
    rel: str
    status: str
    seconds: float = 0.0
    reason: str = ""
    output: str = ""


def relpath(path: Path, base: Path) -> str:

    return os.path.relpath(path, base)


def find_projects(root: Path) -> list[Path]:

    found: list[Path] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = list(directory.iterdir())
        except OSError as exc:
            logger.warning("cannot scan {}: {}", directory, exc)
            continue
        if any(entry.name in MARKERS for entry in entries):
            found.append(directory)
        for entry in entries:
            try:
                if (
                    entry.is_dir()
                    and not entry.is_symlink()
                    and entry.name not in SKIP_DIRS
                    and not entry.name.endswith(".egg-info")
                ):
                    stack.append(entry)
            except OSError:
                continue
    return sorted(found)


def is_buildable(directory: Path) -> bool:
    if (directory / "setup.py").is_file():
        return True
    if tomllib is None:
        return True
    try:
        with open(directory / "pyproject.toml", "rb") as stream:
            data = tomllib.load(stream)
    except tomllib.TOMLDecodeError:
        return True
    except OSError:
        return False
    return "project" in data or "build-system" in data


def kill_tree(process: subprocess.Popen) -> None:

    with contextlib.suppress(OSError, ProcessLookupError):
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                check=False,
            )
            process.kill()


def build_one(task: tuple[str, str], *, out_root: str | None, no_isolation: bool, timeout: int) -> Result:

    path_str, rel = task
    directory = Path(path_str)
    started = time.perf_counter()

    def elapsed() -> float:
        return time.perf_counter() - started

    try:
        if not is_buildable(directory):
            return Result(rel, "skipped", reason="pyproject.toml has no [project] or [build-system]")
        with tempfile.TemporaryDirectory(prefix="pkgbuild_") as scratch:
            if out_root:
                flat = "root" if rel == "." else rel.replace(os.sep, "__")
                outdir = Path(out_root) / flat
                outdir.mkdir(parents=True, exist_ok=True)
            else:
                outdir = Path(scratch)
            command = [sys.executable, "-m", "build", "--outdir", str(outdir)]
            if no_isolation:
                command.append("--no-isolation")
            command.append(".")
            process = subprocess.Popen(
                command,
                cwd=directory,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                start_new_session=(os.name == "posix"),
            )
            try:
                output, _ = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                kill_tree(process)
                output, _ = process.communicate()
                return Result(rel, "failed", elapsed(), f"timed out after {timeout}s", tail(output))
            except BaseException:
                kill_tree(process)
                raise
            if process.returncode != 0:
                return Result(rel, "failed", elapsed(), f"exit code {process.returncode}", tail(output))
            return Result(rel, "ok", elapsed())
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        return Result(rel, "failed", elapsed(), f"{type(exc).__name__}: {exc}")


def tail(text: str | None) -> str:
    lines = (text or "").strip().splitlines()
    return "\n".join(lines[-TAIL_LINES:])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build every Python project under the current directory.")
    parser.add_argument("--out", metavar="DIR", help="keep built artifacts here (default: discard)")
    parser.add_argument("--no-isolation", action="store_true", help="build in the current environment")
    parser.add_argument("--timeout", type=int, default=900, metavar="SEC", help="per-project timeout (default: 900)")
    parser.add_argument("--log-file", metavar="FILE", help="also write errors to this file")
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error("--timeout must be at least 1")
    return args


def main() -> int:
    args = parse_args()
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level: <8}</level> {message}")
    if args.log_file:
        logger.add(args.log_file, level="ERROR", encoding="utf-8")
    if importlib.util.find_spec("build") is None:
        logger.error("the 'build' package is not installed (pip install build)")
        return 1
    root = Path.cwd()
    out_root = str(Path(args.out).resolve()) if args.out else None
    projects = find_projects(root)
    if not projects:
        print("No setup.py or pyproject.toml found.")
        return 1
    tasks = [(str(project), relpath(project, root)) for project in projects]
    print(f"Found {len(tasks)} project(s); building with {WORKERS} workers.\n")
    worker = functools.partial(build_one, out_root=out_root, no_isolation=args.no_isolation, timeout=args.timeout)
    ok: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []
    try:
        with mp.Pool(processes=WORKERS) as pool:
            for result in pool.imap_unordered(worker, tasks):
                if result.status == "ok":
                    ok.append(result.rel)
                    print(f"[ OK ] {result.rel}  ({result.seconds:.1f}s)")
                elif result.status == "skipped":
                    skipped.append(result.rel)
                    print(f"[SKIP] {result.rel}  ({result.reason})")
                else:
                    failed.append(result.rel)
                    print(f"[FAIL] {result.rel}  ({result.reason})")
                    logger.error("build failed: {} ({})\n{}", result.rel, result.reason, result.output or "<no output>")
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    print("\n" + "=" * 60)
    print(f"Built successfully ({len(ok)}):")
    for rel in sorted(ok):
        print(f"  {rel}")
    print(f"\nFailed ({len(failed)}):")
    for rel in sorted(failed):
        print(f"  {rel}")
    if skipped:
        print(f"\nSkipped, not a package ({len(skipped)}):")
        for rel in sorted(skipped):
            print(f"  {rel}")
    return 1 if failed else 0


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
