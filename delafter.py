#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a text file path and a single target character from the command line, then rewrites that same file in place with a cleaned version of its contents. For each line of the file, the script should remove surrounding whitespace and discard lines that are empty after trimming. If a line contains the target character, everything from the first occurrence of that character onward should be cut off, keeping only the text before it. Lines without the target character should be kept as their trimmed form. The remaining lines should be saved back to the original file, joined by newlines and encoded as UTF-8. If no lines remain after processing, the file should be left unchanged. The script should accept the file path and the target character as its two command-line arguments and run only when executed directly.
---"""

from __future__ import annotations
from pathlib import Path
import sys


def read_lines(path):
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


if __name__ == "__main__":
    file_name = Path(sys.argv[1])
    nl = []
    target_char = sys.argv[2]
    for line in read_lines(file_name):
        stripped = line.strip()
        if stripped and target_char in stripped:
            indx = stripped.index(target_char)
            cleaned = stripped[:indx]
            nl.append(cleaned)
        elif stripped:
            nl.append(stripped)
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")
