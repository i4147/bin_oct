#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that takes a file path as a command-line argument and prints the first 1024 bytes of its contents.
The script should attempt to open and read the file as UTF-8 text, ignoring any decoding errors, and print the resulting text.
If this text-mode read fails for any reason, it should fall back to opening the file in binary mode and printing the raw first 1024 bytes instead."""

from __future__ import annotations
from pathlib import Path
import sys


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    try:
        with fn.open(encoding="utf-8", errors="ignore") as f:
            print(f.read(1024))
    except:
        with fn.open("rb") as f:
            print(f.read(1024))
