#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that checks whether brackets, braces, and parentheses are balanced in one or more source files.
It should accept file paths as command-line arguments, or if none are given, discover all ".py" files in the current directory via a helper "get_files" function from a local "dh" module.
For each file, read its text and use a stack-based algorithm to verify matching of "()", "[]", and "{}", printing the filename when the file's brackets are fully balanced.
When multiple files are provided, process them concurrently using a multiprocessing Pool (spawn context, 8 workers) with a bounded pending-task queue (max size 16) to limit memory usage, while single-file input is processed synchronously."""

from __future__ import annotations
import sys
from collections import deque
from multiprocessing import get_context
from pathlib import Path
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
