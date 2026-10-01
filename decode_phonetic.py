#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that takes a file path as its single argument, reads the file's text content using UTF-8 encoding with error replacement for invalid bytes, decodes any HTML entities in that content using the standard library's unescape function, and then overwrites the same file in place with the unescaped text.
The script should run as a standalone module invoked via the command line, using sys.argv to obtain the target file path and pathlib.Path for file reading and writing.
It should exit cleanly by returning None from main through SystemExit."""

import sys
from html import unescape
from pathlib import Path


def main() -> None:
    fn = Path(sys.argv[1])
    content = fn.read_text(encoding="utf-8", errors="replace")
    fn.write_text(unescape(content), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
