#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that takes a requirements.txt file path as its single argument, reads its lines, and cleans each entry by stripping comments, environment markers (after ";"), extras (e.g.
"[extra]"), and version specifiers (==, >=, <=, ~=, !=, ===, <, >), leaving only the bare package name.
It should remove empty lines and duplicate entries, then sort the resulting package names case-grouped (uppercase-starting names first, lowercase-starting next, others last, alphabetically within each group).
The script should overwrite the original file with the cleaned, sorted list (one package per line) and also print the cleaned list to stdout under a "=== Cleaned Requirements ===" header.
Handle missing file errors and incorrect usage by printing a helpful message to stderr and exiting with status code 1."""

from __future__ import annotations
from pathlib import Path
import re
import sys


_VERSION_OP_RE = re.compile(r"\s*(?:===|==|!=|>=|<=|~=|>|<)\s*")


def clean_requirement(line: str) -> str:
    line = line.split("#", 1)[0].strip()
    if not line:
        return ""
    line = line.split(";", 1)[0].strip()
    if not line:
        return ""
    line = re.sub(r"\[.*?\]", "", line).strip()
    if not line:
        return ""
    parts = _VERSION_OP_RE.split(line, maxsplit=1)
    return parts[0].strip()


def group_key(name: str) -> tuple[int, str]:
    first = name[0]
    if first.isupper():
        return 0, name
    if first.islower():
        return 1, name
    return 2, name


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} requirements.txt", file=sys.stderr)
        sys.exit(1)
    fname = sys.argv[1]
    try:
        with Path(fname).open(encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{fname}' not found.", file=sys.stderr)
        sys.exit(1)
    cleaned = []
    seen = set()
    for line in lines:
        c = clean_requirement(line)
        if c and c not in seen:
            cleaned.append(c)
            seen.add(c)
    cleaned = sorted(cleaned, key=group_key)
    with Path(fname).open("w", encoding="utf-8") as f:
        f.writelines(item + "\n" for item in cleaned)
    print("\n=== Cleaned Requirements ===")
    for item in cleaned:
        print(item)


if __name__ == "__main__":
    raise SystemExit(main())
