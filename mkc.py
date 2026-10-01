#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that takes a single C or C++ source file path as an argument and compiles it into a stripped executable.
The script should verify the file exists, choose clang for .c files and clang++ for .cpp files, and reject any other extension with an error.
It should compile the source into an output binary named after the file's stem, then run the strip command on the resulting binary to remove debug symbols, printing status messages for each successful step.
If compilation fails, it should print the captured stderr output and exit with a non-zero status code, and it should also print a usage message and exit if no source file argument is provided."""

import subprocess
import sys
from pathlib import Path


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
