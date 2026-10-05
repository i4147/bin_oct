#!/data/data/com.termux/files/usr/bin/python3.12
# build_all.py: try building every Python project under the current dir, 4 at a time.
#
# Requires: pip install build loguru
# Usage   : python build_all.py                  (artifacts are built into temp dirs and discarded)
#           python build_all.py --out dist_all   (keep artifacts in dist_all/<relpath with "__">)
#           python build_all.py --no-isolation   (use the current env, no network for build deps)
#
# Design notes
#  - A "project" is a dir containing setup.py or pyproject.toml. Junk dirs (venvs, VCS, caches,
#    build/dist, node_modules, *.egg-info) are pruned during the walk so they are never scanned.
#  - Dirs whose pyproject.toml has neither [project] nor [build-system] (tool config only, e.g. a
#    lone [tool.ruff]) and that have no setup.py are reported as SKIPPED, not as failures.
#    Invalid TOML is NOT skipped; the build runs and reports the real error.
#  - Exactly 4 workers via mp.Pool(4).imap_unordered; each worker runs `python -m build` in a
#    subprocess. Workers never log; they return a Result and the parent logs with loguru. This
#    avoids loguru handler problems under the "spawn" start method (Windows/macOS).
#  - Each build gets its own session so a timeout can kill the whole process tree (pip, backends).
#  - A setup.py build may still create *.egg-info inside the source folder; that is setuptools
#    behavior, not something this script controls.
#  - Exit codes: 0 all built (or skipped), 1 some failed or setup error, 130 Ctrl-C.

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
    import tomllib  # Python 3.11+
except ImportError:  # older Pythons: treat every pyproject.toml as buildable
    tomllib = None

WORKERS = 4  # fixed, as requested
MARKERS = ("setup.py", "pyproject.toml")
SKIP_DIRS = frozenset(
    {
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
    }
)
TAIL_LINES = 40  # how much build output to keep for the error log


@dataclass(frozen=True, slots=True)
class Result:
    rel: str
    status: str  # "ok" | "failed" | "skipped"
    seconds: float = 0.0
    reason: str = ""  # one-line summary
    output: str = ""  # tail of build output, failures only


def relpath(path: Path, base: Path) -> str:
    # os.path.relpath handles "not a subpath" cases that Path.relative_to would raise on.
    return os.path.relpath(path, base)


def find_projects(root: Path) -> list[Path]:
    # Iterative walk with pruning; rglob would descend into venvs and node_modules first.
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
                    and not entry.is_symlink()  # symlinks could loop or escape the tree
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
        return True  # let the build surface the syntax error as a failure
    except OSError:
        return False
    return "project" in data or "build-system" in data


def kill_tree(process: subprocess.Popen) -> None:
    # Kill the build and everything it spawned (pip, compilers, backends).
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
    # Runs in a worker process. Must never raise: one bad project may not abort the whole run.
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
                stdin=subprocess.DEVNULL,  # a build must never block waiting for input
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
            except BaseException:  # Ctrl-C or worker termination: do not leave orphan builds
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
        # Fixed pool of 4; imap_unordered yields each result as soon as its build finishes.
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
