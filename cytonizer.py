#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python script that batch-compiles Cython source files in parallel, and describe it so an AI coding agent can rebuild it from scratch.

The script is a command-line tool for Termux (Android, Python at `/data/data/com.termux/files/usr/bin/env python`). It runs with `ations` and has a module-level constant for the number of worker processes, set to 4. It also records the directory it was started in as a module-level variable.

Dependencies:
- Standard library only for path handling, OS interaction, and argument parsing.
- Two helpers imported from a local module named `dh`:
  - `get_files(directory, ext=[...])` returns a list of files under a directory matching the given extensions.
  - `mpf(function, iterable)` runs a function over an iterable in parallel and returns the results- Reproduce these two helpers as needed, or import them from `dh` if that module is present. The worker count of `mpf` should follow the module-level constant.

Behavior:
- `process_file(path)` takes a file path, converts it to a `Path`, changes the current working directory to that file's parent directory, then runs the external shell command `cythonize` on the file's bare name via does not check the return code. It returns nothing.
- `main()` determines the input file list:
  - If command-line arguments are given, each argument is handled as follows: an existing file is added directly; an existing directory is searched recursively for `.pyx` files and those are added. Anything else is silently ignored.
  - If no arguments are given, all `.pyx` files under the current working directory are used.
  - The collected file list is passed to `mpf(process_file, files)` for parallel processing. The result is discarded.
- The script entry point calls `main()` and passes its return value to `SystemExit`, so the process exits with status 0 on normal completion.

Edge cases and notes:
- Relative paths from arguments are resolved against the current working directory at the time of checking.
- Because `process_file` changes directory, multiple parallel workers each change their own process's working directory. Compilation then happens relative to each file's own folder.
- Duplicate entries are not removed if the same file is given twice or reached through overlapping directory arguments.
- No logging, no progress output beyond what `cythonize` prints, and no explicit exception handling for missing `cythonize`, unreadable paths, or failed compilations.
- The script should be written as a single file with a Termux-style shebang line, using clean names and minimal comments in keeping with a small utility script.
---"""

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
