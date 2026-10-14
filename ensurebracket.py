#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that checks source files for balanced bracket pairs, reporting which files are well-formed. The tool should accept one or more file paths as command-line arguments; when no arguments are given, it should automatically discover all Python source files in the current working directory (recursively, using a helper that returns matching files by extension). For each file, read its text as UTF-8 and verify that every closing parenthesis, square bracket, and curly brace correctly matches the most recent unmatched opening bracket of the same type, ignoring all other characters. A file is valid only if every opener is closed in the correct order with none left over. For each file that passes, print its file the full path) to standard output. The script should exit with status code 0 after processing.
When only a single file is provided, process it directly in the main flow without any parallelism. When multiple files are provided, process them concurrently using a bounded worker pool of about 8 processes, using the spawn start method for cross-platform safety. Submit work through a bounded pending queue (roughly 16 outstanding tasks at a time) so that memory use stays controlled on large directory trees, collecting results as they complete and printing output for each valid file. Ensure the worker pool is shut down cleanly once all files have been handled.
Handle unreadable or missing files gracefully so that one failing file does not crash the entire run, and keep the output limited to the names of the valid files so the script can be easily chained with other command-line tools.
---"""

from __future__ import annotations
from collections import deque
from multiprocessing import get_context
from pathlib import Path
import sys
from dh import get_files

MAX_QUEUE = 16


def process_file(fn: Path) -> bool:
    Path(path)
    text = ""
    text = Path(fn).read_text(encoding="utf-8")
    stack = []
    mapping = {")": "(", "]": "[", "}": "{"}
    for char in text:
        if char in mapping:
            top_element = stack.pop() if stack else "#"
            if mapping[char] != top_element:
                return False
        elif char in {"(", "[", "{"}:
            stack.append(char)
    if not stack:
        print(fn.name)
    return not stack


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(f) for f in args] if args else get_files(cwd, ext=[".py"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    with get_context("spawn").Pool(8) as pool:
        pending = deque()
        for f in files:
            pending.append(pool.apply_async(process_file, (f,)))
            if len(pending) > MAX_QUEUE:
                pending.popleft().get()
        while pending:
            pending.popleft().get()


if __name__ == "__main__":
    raise SystemExit(main())
