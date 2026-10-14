#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory for C and C++ source files (.c and .cpp), compiles each one in parallel using an external compiler command, and reports the outcome of every compilation.
The script should:
- Discover all C source files and all C++ source files throughout the directory tree beneath the starting location, and display the directory being scanned before processing begins.
- Choose an appropriate compiler for each source file type (a C compiler for .c files and a C++ compiler for .cpp files), and produce an executable output placed alongside its source file, named after the source file without its extension.
- Run compilations concurrently across multiple worker processes to take advantage of multiple CPU cores.
- Enforce a per-file time limit so that a hanging compilation is terminated and reported as a timeout rather than blocking the whole run.
- Capture compiler output and error messages, and treat any non-zero exit status as a failure whose error details are shown to the user.
- Handle unexpected exceptions for individual files gracefully so that one failing file never stops the others from being processed.
- Print a clear, human-readable status line for each file as results arrive, using distinct markers for success, compilation failure, timeout, and other errors.
- After all tasks finish, print a concise summary showing the total number of files processed, how many compiled successfully, and how many failed.
- Run its main logic only when executed directly as a program, and ensure it behaves correctly on all major operating systems.
The output should be a self-contained, robust command-line tool that requires no arguments and works out of the box in any project directory.
---"""

from __future__ import annotations
from multiprocessing import Pool
from pathlib import Path
import subprocess
import sys


def compile_file(args):
    path, compiler, output_path = args
    try:
        cmd = [compiler, str(path), "-o", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return (
                str(path),
                True,
                f"✓ Compiled: {path.name} -> {output_path.name}",
            )
        else:
            return (
                str(path),
                False,
                f"✗ Failed: {path.name}\n{result.stderr}",
            )
    except subprocess.TimeoutExpired:
        return (str(path), False, f"✗ Timeout: {path.name}")
    except Exception as e:
        return (str(path), False, f"✗ Error: {path.name} - {e!s}")


def main():
    root_dir = Path.cwd()
    print(f"Scanning directory: {root_dir}\n")
    c_files = list(root_dir.rglob("*.c"))
    cpp_files = list(root_dir.rglob("*.cpp"))
    tasks = []
    for c_file in c_files:
        output_path = c_file.with_suffix("")
        tasks.append((c_file, "clang", output_path))
    for cpp_file in cpp_files:
        output_path = cpp_file.with_suffix("")
        tasks.append((cpp_file, "clang++", output_path))
    if not tasks:
        print("No .c or .cpp files found.")
        return
    print(f"Found {len(c_files)} .c file(s) and {len(cpp_files)} .cpp file(s)")
    print(f"Starting compilation with 4 workers...\n")
    with Pool(processes=4) as pool:
        results = pool.map(compile_file, tasks)
    print("\n" + "=" * 40)
    print("Compilation Results:")
    print("=" * 40 + "\n")
    successful = 0
    failed = 0
    for _path, success, message in results:
        print(message)
        if success:
            successful += 1
        else:
            failed += 1
    print("\n" + "=" * 40)
    print(f"Summary: {successful} successful, {failed} failed")
    print("=" * 40)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    raise SystemExit(main())
