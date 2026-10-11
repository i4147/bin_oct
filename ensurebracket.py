#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script that checks whether the bracket pairs in source files are balanced, and reproduce it exactly as described below.

**Purpose:** The script scans text files and reports which ones have unbalanced or mismatched brackets. It only considers the three bracket pairs: parentheses `()`, square brackets `[]`, and curly braces `{}`. Nothing else in the file matters, including brackets inside strings or comments.

**Shebang and imports:** Start with a Termux-style shebang line pointing to `/data/data/com.termux/files/usr/bin/env python`. Begin the module with `from __future__ import annotations`. Use the standard library modules `sys`, `collections.deque`, `multiprocessing.get_context`, and `pathlib.Path`. Also import a helper named `get_files` from a local module called `dh`. That helper takes a directory and an `ext` keyword argument (a list of extensions such as `[".py"]`) and returns the matching file paths. Do not implement `get_files` yourself; just import it.

**Constants:** Define `MAX_QUEUE = 16` at module level. It limits how many asynchronous results can be pending at once.

**`process_file(fn: Path) -> bool` behavior:**
- Read the file as UTF-8 text using `Path(fn).read_text(encoding="utf-8")`.
- Maintain a stack. Iterate over every character. When a character is an opening bracket `(`, `[`, or `{`, push it. When it is a closing bracket `)`, `]`, or `}`, pop the top of the stack (use the sentinel `"#"` if the stack is empty) and compare it against the matching opener from a mapping dictionary. If they differ, return `False` immediately. Ignore all other characters.
- After the scan, if the stack is empty, print the file's name only (`fn.name`, not the full path) to standard output.
- Return `True` if the stack is empty, otherwise `False`. Note that an unclosed opener at end-of-file counts as unbalanced, so the name is printed only when balanced, and the return value is the balanced flag.
- Do not add any other error handling beyond what is described; let file read errors propagate.
- Be careful: the function should behave exactly as described, including printing the name only on success.

**`main() -> None` behavior:**
- Get the current working directory with `Path.cwd()`.
- Take command-line arguments from `sys.argv[1:]`. If any are given, convert each to a `Path`. If none are given, call `get_files(cwd, ext=[".py"])` to find Python files in the current directory.
- If exactly one file is present, call `process_file` on it directly in the main process, then exit with status 0 via `sys.exit(0)`. Do not use multiprocessing for a single file.
- Otherwise, create a process pool using the `"spawn"` start method via `get_context("spawn").Pool(8)`, with 8 workers, used as a context manager.
- Use a `deque` as a sliding window of pending async results. For each file, submit `pool.apply_async(process_file, (f,))` and append the result handle. If the deque grows beyond `MAX_QUEUE`, pop the oldest result from the left and call `.get()` on it to wait for it (this propagates any exception and bounds memory use).
- After submitting all files, drain the remaining deque by calling `.get()` on each pending result in order.
- The function returns nothing.

**Entry point:** Under `if __name__ == "__main__":`, run `main()` and raise `SystemExit` with its return value, written as `raise SystemExit(main())`.

**Notable behavior and edge cases to preserve:**
- Output is just the base filename of each balanced file, one per line, printed by the worker processes.
- Multiprocessing with the `spawn` method requires the worker function to be importable at module top level, so `process_file` must stay at module scope.
- The multi-file path ignores the boolean return values from workers; only their printed output matters, and exceptions are surfaced through `.get()`.
- Empty files count as balanced and are printed.
- Non-ASCII content must be read correctly because of the explicit UTF-8 encoding.
- Keep the code concise and idiomatic, using type hints as shown (`Path`, `-> bool`, `-> None`), and avoid extra features such as argument parsing libraries, logging, or extra output formats.
---"""

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
