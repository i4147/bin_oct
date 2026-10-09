#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that recursively compiles Python source files in the current directory (or specific files passed as command-line arguments) into bytecode using compileall, skipping files inside .git directories and nonexistent paths.
It should distribute compilation work across a multiprocessing pool of 8 worker processes with a bounded task queue (max 4 pending) to limit memory usage, using the "spawn" start method.
Before and after compilation, it measures the total disk size of the current working directory via helper functions (gsz, fsz, get_files) imported from a local "dh" module, then prints the net space change with a "+" or "-" sign and a human-readable size format.
"""

from __future__ import annotations
import compileall
import sys
from collections import deque
from multiprocessing import get_context
from pathlib import Path
from dh import fsz, get_files, gsz

MAX_QUEUE = 4


def process_file(path) -> bool | None:
    path = Path(path)
    if not path.exists():
        return False
    if ".git" in path.parts:
        return None
    compileall.compile_file(path, legacy=False, optimize=0)
    return True


def main() -> None:
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    files = [Path(f) for f in args] if args else get_files(cwd, ext=[".py"])
    with get_context("spawn").Pool(8) as pool:
        pending = deque()
        for f in files:
            pending.append(pool.apply_async(process_file, (f,)))
            if len(pending) > MAX_QUEUE:
                pending.popleft().get()
        while pending:
            pending.popleft().get()
    after = gsz(cwd)
    diff_size = before - after
    if after > before:
        sign = "+"
    elif before > after:
        sign = "-"
    print(f"space changed : {sign} {fsz(diff_size)}")


if __name__ == "__main__":
    raise SystemExit(main())
