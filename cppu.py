#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line utility that recursively formats source code files (Java, C/C++/headers, JS, JSON) in the current directory using clang-format with the LLVM style, in-place.
It should accept optional file path arguments on the command line to format specific files instead of auto-discovering them via a helper function, and print the number of files found before processing.
Processing should run in parallel across multiple files using a multiprocessing helper, each file's size before/after formatting should be compared and reported, and the script should print the total disk space change (in human-readable size) for the working directory after formatting completes.
It relies on a local "dh" module providing helper functions for colored printing, file discovery, size measurement/formatting, size-change reporting, multiprocessing, and running external commands, and it should silently skip files that fail to format."""

from __future__ import annotations
import sys
from pathlib import Path
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
