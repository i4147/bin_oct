#!/data/data/com.termux/files/usr/bin/env python
"""Compile C/C++ sources (and Cythonize .pyx files) in parallel.

Analysis / deduplication
------------------------
- ``compile_c_cpp_files.py`` and ``crun.py`` both walk a tree compiling
  every ``.c``/``.cpp`` file with clang/clang++; ``crun.py`` is broken
  (it calls an undefined ``run_command`` and may leave ``cmd`` unbound).
  Both are now the ``build`` command.
- ``mkc.py`` is the single-file special case (including its ``strip``
  step) -> ``build file.c --strip``.
- ``cytonizer.py`` (runs ``cythonize`` per ``.pyx``) is ``cythonize``.
- The private ``dh`` helpers (file walking, parallel map) are replaced
  by ``pathlib`` + ``concurrent.futures`` from the standard library.

Examples
--------
  python3 c_build_tool.py build                 # all .c/.cpp below .
  python3 c_build_tool.py build src/main.c --strip
  python3 c_build_tool.py build -j 8 --cflags=-O2
  python3 c_build_tool.py cythonize pkg/
"""


import argparse
import shlex
import subprocess
import sys
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WORKERS: int = 4
TIMEOUT_SECONDS: int = 60
COMPILERS: dict[str, str] = {".c": "clang", ".cpp": "clang++", ".cc": "clang++", ".cxx": "clang++"}
SKIP_DIRS: frozenset[str] = frozenset({".git", "__pycache__", "venv", ".venv"})


@dataclass(slots=True)
class JobResult:
    """Result of one external command."""

    source: Path
    ok: bool
    message: str


def collect_sources(inputs: Sequence[Path], suffixes: frozenset[str]) -> list[Path]:
    """Collect source files from file/dir arguments (default: current dir)."""
    roots: list[Path] = list(inputs) or [Path.cwd()]
    found: set[Path] = set()
    for root in roots:
        if root.is_file():
            if root.suffix.lower() in suffixes:
                found.add(root)
        elif root.is_dir():
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in suffixes and not SKIP_DIRS.intersection(path.parts):
                    found.add(path)
    return sorted(found)


def compile_one(job: tuple[Path, str, tuple[str, ...], bool]) -> JobResult:
    """Compile one C/C++ file; output is the source path without suffix."""
    source, _unused, flags, strip = job
    compiler: str = COMPILERS[source.suffix.lower()]
    output: Path = source.with_suffix("")
    try:
        proc = subprocess.run([compiler, str(source), "-o", str(output), *flags],
                              capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return JobResult(source, False, f"timeout: {source.name}")
    except FileNotFoundError:
        return JobResult(source, False, f"compiler not found: {compiler}")
    if proc.returncode != 0:
        return JobResult(source, False, f"failed: {source.name}\n{proc.stderr}")
    if strip:
        subprocess.run(["strip", str(output)], capture_output=True)
    return JobResult(source, True, f"compiled: {source.name} -> {output.name}")


def cythonize_one(source: Path) -> JobResult:
    """Run ``cythonize`` in the directory containing one ``.pyx`` file."""
    try:
        proc = subprocess.run(["cythonize", source.name], cwd=source.parent,
                              capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    except FileNotFoundError:
        return JobResult(source, False, "cythonize not found (pip install Cython)")
    except subprocess.TimeoutExpired:
        return JobResult(source, False, f"timeout: {source.name}")
    if proc.returncode != 0:
        return JobResult(source, False, f"failed: {source.name}\n{proc.stderr}")
    return JobResult(source, True, f"cythonized: {source.name}")


def run_parallel(jobs: Sequence[JobResult] | list[tuple[Path, str, tuple[str, ...], bool]],
                 worker: str, workers: int) -> int:
    """Run *worker* over *jobs*, print results, return the failure count."""
    fn = compile_one if worker == "compile" else cythonize_one
    failed: int = 0
    with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(fn, job) for job in jobs]  # type: ignore[arg-type]
        for future in as_completed(futures):
            result: JobResult = future.result()
            print(("OK  " if result.ok else "FAIL") + f" {result.message}")
            failed += 0 if result.ok else 1
    return failed


def cmd_build(args: argparse.Namespace) -> int:
    """Run the ``build`` subcommand."""
    sources = collect_sources(args.paths, frozenset(COMPILERS))
    if not sources:
        print("No .c/.cpp files found.")
        return 0
    flags: tuple[str, ...] = tuple(shlex.split(args.cflags))
    jobs: list[tuple[Path, str, tuple[str, ...], bool]] = [(s, "", flags, args.strip) for s in sources]
    print(f"Compiling {len(sources)} file(s) with {args.workers} worker(s)...")
    failed: int = run_parallel(jobs, "compile", args.workers)
    print(f"Summary: {len(sources) - failed} ok, {failed} failed")
    return 1 if failed else 0


def cmd_cythonize(args: argparse.Namespace) -> int:
    """Run the ``cythonize`` subcommand."""
    sources = collect_sources(args.paths, frozenset({".pyx"}))
    if not sources:
        print("No .pyx files found.")
        return 0
    failed: int = run_parallel(sources, "cython", args.workers)  # type: ignore[arg-type]
    print(f"Summary: {len(sources) - failed} ok, {failed} failed")
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description="Parallel C/C++/Cython builder (clang by default).")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("build", "Compile .c/.cpp files"), ("cythonize", "Cythonize .pyx files")):
        child = sub.add_parser(name, help=help_text)
        child.add_argument("paths", nargs="*", type=Path, help="Files or dirs (default: current dir)")
        child.add_argument("-j", "--workers", type=int, default=DEFAULT_WORKERS,
                           help="Parallel workers (default: 4)")
    build = sub.choices["build"]
    build.add_argument("--strip", action="store_true", help="Strip each binary after compiling")
    build.add_argument("--cflags", default="", help='Extra compiler flags, e.g. --cflags="-O2 -Wall"')
    sub.choices["build"].set_defaults(handler=cmd_build)
    sub.choices["cythonize"].set_defaults(handler=cmd_cythonize)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    args: argparse.Namespace = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    sys.exit(main())
