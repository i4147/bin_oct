#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line text filter for a file. It takes three arguments: a mode flag, a path to a UTF-8 text file, and a single delimiter character. The script reads the file line by line and, for each line, ignores surrounding whitespace and then splits the line at the first occurrence of the delimiter. In one mode, it keeps only the text before the delimiter; in the other mode, it keeps only the text after the delimiter. If a non-blank line does not contain the delimiter, the whole trimmed line is kept unchanged. Blank lines and lines that produce empty results are discarded. The script should collect the surviving results in order and then output them, one per line, to standard output, so the user can redirect or pipe the result. Handle invalid or missing arguments gracefully with a brief usage message, and handle unreadable or missing files with a clear error message and a non-zero exit status. Keep the implementation simple, dependency-free, and suitable for use in shell pipelines.
---"""

from __future__ import annotations
from pathlib import Path
import sys


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def process_a(line: str, target_char: str) -> str:
    stripped = line.strip()
    if stripped and target_char in stripped:
        indx = stripped.index(target_char)
        return stripped[:indx]
    elif stripped:
        return stripped
    return ""


def process_b(line: str, target_char: str) -> str:
    stripped = line.strip()
    if stripped and target_char in stripped:
        indx = stripped.index(target_char)
        return stripped[indx + 1 :]
    elif stripped:
        return stripped
    return ""


if __name__ == "__main__":
    mode = sys.argv[1]
    file_name = Path(sys.argv[2])
    target_char = sys.argv[3]
    nl: list[str] = []
    for line in read_lines(file_name):
        if mode == "-a":
            result = process_a(line, target_char)
        else:
            result = process_b(line, target_char)
        if result:
            nl.append(result)
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")
