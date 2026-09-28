#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that searches the current directory for a README file (checking common names like README.md, README.rst, README.txt, or README in a case-insensitive manner) and displays its contents using a pager, similar to the `pydoc` command's paging behavior.
If no README file is found, it should print an error message to stderr and exit with status code 1.
The script should read the file as UTF-8 text, falling back to replacing invalid characters if a decoding error occurs."""

import pydoc
import sys
from pathlib import Path

README_CANDIDATES = ["README.md", "README.rst", "README.txt", "README"]


def find_readme() -> Path | None:
    files = {p.name.lower(): p for p in Path().iterdir() if p.is_file()}
    for name in README_CANDIDATES:
        p = files.get(name.lower())
        if p:
            return p
    return None


def main() -> None:
    readme = find_readme()
    if not readme:
        print("No README file found in current directory.", file=sys.stderr)
        sys.exit(1)
    try:
        text = readme.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = readme.read_text(errors="replace")
    pydoc.pager(text)


if __name__ == "__main__":
    raise SystemExit(main())
