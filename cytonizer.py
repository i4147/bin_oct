#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a batch build helper for Cython extension sources. The script should accept zero or more command-line arguments, where each argument may be either a path to an individual Cython source file or a directory. When given a directory, it should discover all Cython source files within it; when given a file, it should use that file directly. If no arguments are provided, it should search the current working directory for Cython source files. Each discovered source file should be compiled by invoking the Cython compiler on it from within that file's own directory, so that generputs land alongside the source. The compilation of multiple files should be carried out in parallel using a small pool of worker processes (around four). The script should restore its original working directory when finished, handle missing or invalid paths gracefully, and exit cleanly with a status code when run as the main program. Keep the implementation simple and dependable, relying only on the standard library where practical, and report progress or errors to the user in a concise way.
---"""

from __future__ import annotations
import os
from os import chdir as os_chdir
from pathlib import Path
import sys
from dh import get_files, mpf

START_DIR = Path.cwd()
NUM_PROCESSES = 4


def process_file(path) -> None:
    path = Path(path)
    pardir = path.parent
    os_chdir(pardir)
    os.system(f"cythonize {path.name}")


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = []
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(get_files(p, ext=[".pyx"]))
    else:
        files = get_files(cwd, ext=[".pyx"])
    _ = mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
