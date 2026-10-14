#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a given directory (recursively) for C and C++ source and header files, checks each one for syntax and compiler warnings using the locally installed Clang compilers, and reports the results.
The tool should:
- Accept a directory path (or a list of files) as input and discover all C and C++ files by extension, covering C source files, C++ source files, C header files, and C++ header files. Each category should be checked using an appropriate language standard (for example, C++17 for C++ sources and C11 for C sources).
- Treat C++ source files and C source files differently in compiler settings, and treat header files specially: since headers cannot be compiled on their own, validate them by wrapping or including them in a temporary translation unit so they can be syntax-checked in isolation.
- Enable strict warning flags (such as all and extra warnings) and treat warnings as errors where appropriate for C++ sources, so that any diagnostic causes a failure.
- Run checks in parallel using a configurable pool of worker processes (default around 8) to speed up large codebases, and collect results safely from all workers.
- Capture both the exit status and the combined compiler output for each file, decoding output tolerantly so that unusual bytes never crash the tool.
- Gracefully handle a missing compiler executable by reporting a clear "command not found" style error for that file rather than crashing the whole run.
- Produce a clear, human-readable summary at the end: the number of files checked, number passed, number failed, and the full diagnostic output for each failing file, grouped and sorted by path.
- Exit with a non-zero status code if any file fails, and zero if all pass, so the tool can be used in continuous integration pipelines.
- Include a command-line interface that lets the user optionally override the number of workers and choose the compiler or flags, with sensible defaults requiring no arguments beyond the target path.
---"""

from __future__ import annotations
import multiprocessing as mp
from pathlib import Path
import subprocess
import sys

CPP_EXTS = {".cpp", ".cc", ".cxx"}
C_EXTS = {".c"}
HEADER_CPP_EXTS = {".hpp", ".hh", ".hxx"}
HEADER_C_EXTS = {".h"}
ALL_EXTS = CPP_EXTS | C_EXTS | HEADER_CPP_EXTS | HEADER_C_EXTS
NUM_WORKERS = 8


def run(cmd, input_bytes=None):
    try:
        proc = subprocess.run(
            cmd,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return proc.returncode, proc.stdout.decode(errors="replace")
    except FileNotFoundError as e:
        return 127, f"command not found: {e}"


def check_file(path: Path):
    ext = path.suffix.lower()
    if ext in CPP_EXTS:
        cmd = [
            "clang++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsyntax-only",
            str(path),
        ]
        rc, out = run(cmd)
    elif ext in C_EXTS:
        cmd = ["clang", "-std=c11", "-Wall", "-Wextra", "-fsyntax-only", str(path)]
        rc, out = run(cmd)
    elif ext in HEADER_CPP_EXTS:
        include_line = f'#include "{path.name}"\n'.encode()
        cmd = ["clang++", "-x", "c++", "-fsyntax-only", "-", "-I", str(path.parent)]
        rc, out = run(cmd, input_bytes=include_line)
    elif ext in HEADER_C_EXTS:
        include_line = f'#include "{path.name}"\n'.encode()
        cmd = ["clang", "-x", "c", "-fsyntax-only", "-", "-I", str(path.parent)]
        rc, out = run(cmd, input_bytes=include_line)
    else:
        return path, True, ""
    return path, rc == 0, out


def gather_files(paths):
    files = []
    if not paths:
        cwd = Path.cwd()
        for p in sorted(cwd.iterdir()):
            if p.is_file() and p.suffix.lower() in ALL_EXTS:
                files.append(p)
        return files
    for arg in paths:
        p = Path(arg)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix.lower() in ALL_EXTS:
                    files.append(f)
        elif p.is_file():
            files.append(p)
        else:
            print(f"warning: skipping non-existent path: {arg}", file=sys.stderr)
    return files


def main():
    args = sys.argv[1:]
    files = gather_files(args)
    if not files:
        print("No C/C++/header files found.", file=sys.stderr)
        return 0
    print(f"Checking {len(files)} file(s) with {NUM_WORKERS} workers...", file=sys.stderr)
    failures = 0
    with mp.Pool(processes=NUM_WORKERS) as pool:
        for path, ok, output in pool.imap_unordered(check_file, files):
            if not ok:
                failures += 1
                print(f"\n=== FAIL: {path} ===")
                print(output.rstrip())
    if failures == 0:
        print("\nAll files passed syntax check.", file=sys.stderr)
    else:
        print(f"\n{failures} file(s) failed.", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
