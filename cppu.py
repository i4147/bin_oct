#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that formats C, C++, Java, and JavaScript/JSON source files in place using the LLVM code style via the clang-format command-line tool. The script should accept file paths as command-line arguments; if none are given, it should recursively discover all supported source files (C/C++ headers and sources, Java, JavaScript, and JSON) under the current working directory. It should process the files concurrently for speed, skip or silently ignore any file that fails to format without stopping the overall run, and track the total disk space change across the directory before and after formatting. Display a colored summary at the start showing how many files were found, and when run on a single file, format it and exit with a non-zero status code. When multiple files are processed, report the net change in disk usage in a human-readable format at the end. Keep the script compact, robust to errors, and runnable directly as a standalone command-line utility.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import cprint, fsz, get_files, gsz, mpf, rrs, runcmd

EXT = [
    ".java",
    ".c",
    ".cpp",
    ".cxx",
    ".cc",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
    ".js",
    ".json",
]


def process_file(path):
    path = Path(path)
    before = gsz(path)
    try:
        runcmd(["clang-format", "-i", "--style=LLVM", str(path)], show_output=False)
        after = gsz(path)
        rrs(path, before, after)
        del before, after
        return
    except:
        del before, after
        return


def main() -> None:
    files: list = []
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    files = [Path(arg) for arg in args] if args else get_files(cwd, ext=EXT)
    all_count = len(files)
    cprint(f"{all_count} files found", "cyan")
    if all_count == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)
    after = gsz(cwd)
    dsz = before - after
    print(f"space change: {fsz(dsz)}")


if __name__ == "__main__":
    raise SystemExit(main())
