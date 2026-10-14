#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single text file path from the command line and normalizes unusual whitespace characters in that file in place. The script should read the file as UTF-8 text, tolerating invalid byte sequences by ignoring them. It should replace non-standard space characters (such as non-breaking spaces, typographic en/em spaces, line and paragraph separators, narrow no-break spaces, and ideographic spaces) with a regular ASCII space. It should then remove zero-width characters (such as zero-width space, zero-width non-joiner, zero-width joiner, and byte-order marks) entirely. The cleaned content should be saved back to the same file, encoded as UTF-8. The script should be runnable from the terminal with the file path as its only argument and should perform no other output or transformations beyond this normalization.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys


def normalize_white_space(input_path: str) -> None:
    text = Path(input_path).read_text(encoding="utf-8", errors="ignore")
    cleaned = re.sub(r"[\u00A0\u2000-\u200F\u2028\u2029\u202F\u205F\u3000\uFEFF]", " ", text)
    cleaned = re.sub(r"[\u200B-\u200D\uFEFF]", "", cleaned)
    Path(input_path).write_text(cleaned, encoding="utf-8")


if __name__ == "__main__":
    fname = sys.argv[1]
    normalize_white_space(fname)
