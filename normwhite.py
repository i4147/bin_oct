#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that takes a file path as its single argument, reads the file's text content using UTF-8 encoding (ignoring decode errors), and normalizes irregular whitespace and invisible Unicode characters within it.
It should replace various Unicode space-like characters (such as non-breaking spaces, line/paragraph separators, and other special spacing marks) with a regular ASCII space, and it should strip out zero-width characters (like zero-width space, zero-width joiner/non-joiner, and the byte-order mark) entirely by removing them.
The cleaned text should then overwrite the original file in place, encoded as UTF-8.
The script should be runnable directly, reading the target filename from the first command-line argument."""

import re
import sys
from pathlib import Path


def normalize_white_space(input_path: str) -> None:
    text = Path(input_path).read_text(encoding="utf-8", errors="ignore")
    cleaned = re.sub(r"[\u00A0\u2000-\u200F\u2028\u2029\u202F\u205F\u3000\uFEFF]", " ", text)
    cleaned = re.sub(r"[\u200B-\u200D\uFEFF]", "", cleaned)
    Path(input_path).write_text(cleaned, encoding="utf-8")


if __name__ == "__main__":
    fname = sys.argv[1]
    normalize_white_space(fname)
