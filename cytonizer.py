#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that batch-compiles Cython source files using the `cythonize` command-line tool.
It should accept optional command-line arguments that are file or directory paths; if none are given, it recursively scans the current working directory for `.pyx` files, while explicit directory arguments are also recursively scanned for `.pyx` files and explicit file arguments are used directly.
For each discovered `.pyx` file, the script should change into its parent directory and run `cythonize` on the filename, processing files in parallel using a multiprocessing helper (4 worker processes) alongside a custom file-discovery utility imported from a local module named `dh`."""

from __future__ import annotations

import os
import sys
from os import chdir as os_chdir
from pathlib import Path

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
