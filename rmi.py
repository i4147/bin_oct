#!/data/data/com.termux/files/usr/bin/env python
"""Write a-line script that strips invisible Unicode characters (such as zero-width spaces, BOM, non-breaking spaces, and bidirectional control marks) from text files, preserving normal newlines.
It should accept a list of file paths as command-line arguments; if none are provided, it should fall back to scanning the current working directory for non-binary files using a helper function `get_nobinary` from a local module named `dh`.
For each file, read its content as UTF-8 (ignoring decode errors), remove the invisible characters, and if any were removed, overwrite the file with the cleaned text and print the count of removed characters, otherwise print a message indicating none were found.
"""

from __future__ import annotations
import sys
from pathlib import Path
from dh import get_nobinary

INVISIBLE_CHARS = {
    "\u200b",
    "\u200c",
    "\u200d",
    "\xa0",
    "\xad",
    "\ufeff",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
}


def clean_text(text: str) -> str:
    cleaned = ""
    for c in text:
        if ord(c) == 8204:
            continue
        if c == "\n":
            cleaned += c
            continue
        if c in INVISIBLE_CHARS:
            continue
        cleaned += c
    return cleaned


def process_file(path: Path) -> None:
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    cleaned = clean_text(text)
    removed = len(text) - len(cleaned)
    if removed:
        print(f"{removed} invisible characters removed")
        path.write_text(cleaned, encoding="utf-8")
        return
    print("No invisible characters found")
    return


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_nobinary(cwd)
    for f in files:
        process_file(f)


if __name__ == "__main__":
    raise SystemExit(main())
