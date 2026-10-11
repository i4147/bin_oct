#!/data/data/com.termux/files/usr/bin/env python
"""Write a single self-contained Python script for Termux (Android) that reproduces the following behavior. Begin the file with a Termux-style shebang pointing to the Termux Python interpreter (`/data/data/com.termux/files/usr/bin/env python`), and include `from __future__ import annotations` as the first import after the shebang.

Purpose: The script is a simple command-line line-by-line file reader that pretty-prints each line through an external formatting function. It reads a text file given as the first command-line argument and, for every line, passes the line (including its trailing newline character, unstripped) to a function named `faprint` imported from a module named `faprint` (imported under the alias `pp`), then prints the returned value to standard output.

Inputs:
- One required positional command-line argument: the path to a text file, read from `sys.argv[1]`.
- The file is opened with UTF-8 encoding.

Outputs:
- To stdout, one `print` call per line of the input file, each printing whatever `faprint` returns for that line. Because lines retain their newline, output from `print` will typically contain extra blank lines unless `faprint` strips them; do not alter this behavior.

Structure:
- A helper generator function (named `ylines`) that accepts a `pathlib.Path`, opens it with UTF-8 encoding in a context manager, and uses `yield from` on the file object so lines are streamed lazily rather than loaded into memory at once.
- A `if __name__ == "__main__":` guard containing the main logic: convert `sys.argv[1]` to a `Path`, iterate over `ylines` of that path, and print `pp(line)` for each line.

Dependencies:
- Standard library only: `sys`, `pathlib.Path`, and `__future__` annotations.
- One third-party or local module: `faprint`, providing a callable `faprint` that takes a string and returns a printable value. The script must import it as `from faprint import faprint as pp`; do not implement or stub this function unless asked.

Error handling and edge cases:
- No explicit error handling is present. A missing argument raises `IndexError`; a nonexistent or unreadable file raises `FileNotFoundError`/`OSError`; a file that is not valid UTF-8 raises `UnicodeDecodeError`. Reproduce this behavior faithfully: do not add try/except blocks, validation, or usage messages.
- Empty files produce no output. Files with no trailing newline yield a final line without one.

Execution and usage:
- Run as: `python <script> <file>` (or directly, since it has a shebang and is executable on Termux).
- Keep the script minimal, with no classes, no argparse, no logging, and no additional features.

Deliver the complete script as a single file.
---"""

from __future__ import annotations

import sys
from pathlib import Path

from faprint import faprint as pp


def ylines(path: Path):
    with path.open(encoding="utf-8") as f:
        yield from f


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    for k in ylines(fn):
        print(pp(k))
