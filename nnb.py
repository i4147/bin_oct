#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that operates as a command-line utility for in-place text file transformation. The script must accept exactly one argument: the path to a text file. If the argument count is wrong, it should print a brief usage message showing how to invoke the script and exit with a non-zero status code.
When given a valid file path, the script should read the file's entire contents as UTF-8 text, convert every actual line break into a literal two-character escape sequence (a backslash followed by the letter "n") so that the whole content ends up on a single line, and then write the transformed text back to the same file, overwriting the original contents with UTF-8 encoding. No other characters should be altered, and the script should produce no output on success.
Keep the implementation simple and self-contained, using only the Python standard library, and ensure the script runs as a standalone program when executed directly.
---"""

from __future__ import annotations
from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <filename>")
        sys.exit(1)
    fname = sys.argv[1]
    content = Path(fname).read_text(encoding="utf-8")
    content = content.replace("\n", "\\n")
    Path(fname).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
