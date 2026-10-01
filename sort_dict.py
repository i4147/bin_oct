#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that takes a filename as its sole argument, reads all lines from that text file, and keeps only the lines containing a colon or an equals sign.
For each retained line it derives a sort key from the substring after the first colon (or equals sign, if no colon is present) with surrounding whitespace stripped, printing that extracted value to the console as a side effect.
The script then sorts the filtered lines by this extracted key value and overwrites the original file with the sorted lines using UTF-8 encoding.
File reading should tolerate encoding errors by replacing invalid characters rather than raising an exception."""

import sys
from pathlib import Path


def dict_val(line: str) -> str:
    if ":" in line:
        out = line.split(":", 1)[1].strip()
        print(out)
        return out
    if "=" in line:
        out = line.split("=", 1)[1].strip()
        print(out)
        return out
    return line


def main() -> None:
    fname = sys.argv[1]
    with Path(fname).open(encoding="utf8", errors="replace") as f:
        lines = f.readlines()
    all_lines = [line for line in lines if ":" in line or "=" in line]
    all_lines.sort(key=dict_val)
    with Path(fname).open("w", encoding="utf-8") as fo:
        fo.writelines(all_lines)


if __name__ == "__main__":
    raise SystemExit(main())
