#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line helper for compiling C or C++ source files into native executables. The tool should accept a single source file path as input and automatically choose the appropriate compiler based on the file's extension: a C compiler for `.c` files and a C++ compiler for `.cpp` files. It should reject any other file type with a clear error message.
Before compiling, the tool should verify that the source file exists and exit with a non-zero status and an error written to the error stream if it does not.
The compiled executable should be named after the source file's base name (without its extension) and placed in the current working directory. Compilation output and status messages should be reported to the user, with a success message confirming the source and the produced binary.
After a successful compilation, the tool should reduce the size of the resulting binary by stripping its debugging and symbol information, reporting when this step completes.
If the compiler fails, the tool should report a concise error indicating compilation failed and display the compiler's diagnostic output so the user can see what went wrong, then exit with a non-zero status. Similar handling should apply if the stripping step fails.
The script should be runnable from the command line, taking the source file path as its primary argument, and should be written in clean, well-structured Python with clear user-facing messages and proper exit codes for success and each failure mode.
---"""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys


def compile_file(source_path: str) -> None:
    source = Path(source_path)
    if not source.exists():
        print(f"Error: {source_path} not found", file=sys.stderr)
        sys.exit(1)
    if source.suffix == ".c":
        compiler = "clang"
    elif source.suffix == ".cpp":
        compiler = "clang++"
    else:
        print(f"Error: unsupported file type {source.suffix}", file=sys.stderr)
        sys.exit(1)
    output = source.stem
    compile_cmd = [compiler, str(source), "-o", output]
    try:
        result = subprocess.run(compile_cmd, check=True, capture_output=True, text=True)
        print(f"Compiled {source_path} → {output}")
        strip_cmd = ["strip", output]
        subprocess.run(strip_cmd, check=True, capture_output=True)
        print(f"Stripped {output}")
    except subprocess.CalledProcessError as e:
        print("Error: Compilation failed", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mkc.py <file.c or file.cpp>", file=sys.stderr)
        sys.exit(1)
    compile_file(sys.argv[1])
