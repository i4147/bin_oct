#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans invisible and hidden Unicode characters from text files. The tool should accept one or more file paths as command-line arguments; if no paths are given, it should automatically discover the relevant text files in the current working directory, excluding binary files. For each file, it should read the content as UTF-8 (tolerating malformed bytes), remove zero-width characters, non-breaking and soft hyphens, byte-order marks, and bidirectional control characters while preserving newlines and all visible text, and then write the cleaned content back to the same file only if anything was actually removed. The script should report to the user, per file, how many invisible characters were removed or that none were found, and it should handle missing or unreadable files gracefully without stopping the entire run. Keep the implementation simple, dependency-light, and suitable for running from the command line on any operating system.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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
