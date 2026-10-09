#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python commandes exactly one argument, a filename, and exits with usage instructions and a nonzero status code if the argument is missing or extra arguments are given.
The script should read the file's entire text content as UTF-8, replace every actual newline character with the literal two-character sequence backslash-n, and then overwrite the same file with this modified content.
Use pathlib.Path for file reading and writing, and structure the code with a main() function invoked via SystemExit under the standard __main__ guard."""

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
