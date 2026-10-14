#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a text file path and a target character from the command line, then rewrites that same file in place. For each line, it removes surrounding whitespace and skips lines that are empty after trimming. For lines that contain the target character, it keeps only the portion of the line starting from the first occurrence of that character, discarding everything before it. Lines that do not contain the target character are kept as their trimmed form. Blank lines are dropped entirely. The result should be saved back to the original file as UTF-8 text, with the remaining lines joined by newlines. If no lines remain after processing, the file should be left unchanged rather than being overwritten with empty content. The script should be runnable from the command line as a standalone tool, read the file's contents line by line, and handle the file safely with clear behavior for missing arguments or unreadable files.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import read_lines

THRESHOLD = 1048576
if __name__ == "__main__":
    file_name = Path(sys.argv[1])
    nl = []
    target_char = sys.argv[2]
    for line in read_lines(file_name):
        stripped = line.strip()
        if stripped and target_char in stripped:
            indx = stripped.index(target_char)
            cleaned = stripped[indx:]
            nl.append(cleaned)
        elif stripped:
            nl.append(stripped)
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")
