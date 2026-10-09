#!/data/data/com.termux/files/usr/bin/python
"""
Unified C/C++ Compiler CLI

Provides utilities to recursively compile C/C++ files in a directory
or compile and strip a single file.

Usage Examples:
    python merged.py scan
    python merged.py scan --workers 8 --timeout 120 --size-diff
    python merged.py single main.c
    python merged.py single utils.cpp --no-strip
"""

from __future__ import annotations
import argparse
from multiprocessing import Pool
from pathlib import Path
import subprocess
import sys
from typing import Generator, List, Tuple


def format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_dir_size(directory: Path) -> int:
    return sum(f.stat().st_size for f in directory.rglob("*") if f.is_file())


def should_skip(path: Path) -> bool:
    return any(part.startswith(".") or part == "__pycache__" for part in path.parts)


def find_source_files(directory: Path) -> Generator[Path, None, None]:
    visited = set()
    for p in directory.rglob("*"):
        if p.is_file() and p.suffix in {".c", ".cpp"}:
            resolved = p.resolve()
            if not should_skip(p) and resolved not in visited:
                visited.add(resolved)
                yield p


def compile_file(args_tuple: tuple[Path, str, Path, int]) -> tuple[str, bool, str]:
    src_file, compiler, out_file, timeout = args_tuple
    try:
        cmd = [compiler, str(src_file), "-o", str(out_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return (str(src_file), True, f"✓ Compiled: {src_file.name} -> {out_file.name}")
        return (str(src_file), False, f"✗ Failed: {src_file.name}\n{result.stderr}")
    except subprocess.TimeoutExpired:
        return (str(src_file), False, f"✗ Timeout: {src_file.name}")
    except Exception as e:
        return (str(src_file), False, f"✗ Error: {src_file.name} - {e!s}")


def cmd_scan(workers: int, timeout: int, size_diff: bool) -> None:
    cwd = Path.cwd()
    print(f"Scanning directory: {cwd}\n")

    initial_size = get_dir_size(cwd) if size_diff else 0

    source_files = list(find_source_files(cwd))
    if not source_files:
        print("No .c or .cpp files found.")
        return

    tasks = []
    c_count = 0
    cpp_count = 0

    for src in source_files:
        out_file = src.with_suffix("")
        if src.suffix == ".c":
            tasks.append((src, "clang", out_file, timeout))
            c_count += 1
        elif src.suffix == ".cpp":
            tasks.append((src, "clang++", out_file, timeout))
            cpp_count += 1

    print(f"Found {c_count} .c file(s) and {cpp_count} .cpp file(s)")
    print(f"Starting compilation with {workers} workers...\n")

    with Pool(processes=workers) as pool:
        results = pool.map(compile_file, tasks)

    print("\n" + "=" * 40)
    print("Compilation Results:")
    print("=" * 40 + "\n")

    success = 0
    failed = 0
    for _, is_ok, msg in results:
        print(msg)
        if is_ok:
            success += 1
        else:
            failed += 1

    print("\n" + "=" * 40)
    print(f"Summary: {success} successful, {failed} failed")
    print("=" * 40)

    if size_diff:
        final_size = get_dir_size(cwd)
        diff = final_size - initial_size
        print(f"Size difference: {format_size(diff)}")

    sys.exit(0 if failed == 0 else 1)


def cmd_single(file_path: Path, strip: bool) -> None:
    if not file_path.exists():
        print(f"Error: {file_path} not found", file=sys.stderr)
        sys.exit(1)

    if file_path.suffix == ".c":
        compiler = "clang"
    elif file_path.suffix == ".cpp":
        compiler = "clang++"
    else:
        print(f"Error: unsupported file type {file_path.suffix}", file=sys.stderr)
        sys.exit(1)

    out_name = file_path.stem
    cmd = [compiler, str(file_path), "-o", out_name]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Compiled {file_path} -> {out_name}")

        if strip:
            subprocess.run(["strip", out_name], check=True, capture_output=True)
            print(f"Stripped {out_name}")

    except subprocess.CalledProcessError as e:
        print("Error: Compilation failed", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified C/C++ Compiler CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_scan = subparsers.add_parser("scan", help="Recursively compile C/C++ files in the current directory")
    p_scan.add_argument("-w", "--workers", type=int, default=4, help="Number of worker processes (default: 4)")
    p_scan.add_argument(
        "-t", "--timeout", type=int, default=60, help="Compilation timeout per file in seconds (default: 60)"
    )
    p_scan.add_argument("--size-diff", action="store_true", help="Calculate and print directory size difference")

    p_single = subparsers.add_parser("single", help="Compile a single C/C++ file")
    p_single.add_argument("file", type=Path, help="C or C++ source file to compile")
    p_single.add_argument("--no-strip", action="store_true", help="Do not strip the resulting binary")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(args.workers, args.timeout, args.size_diff)
    elif args.command == "single":
        cmd_single(args.file, not args.no_strip)


if __name__ == "__main__":
    main()
