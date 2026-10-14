#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a file path as a command-line argument and prints the first 1024 characters of that file to the standard output. The script should read the file as text using UTF-8 encoding, tolerating any undecodable bytes by ignoring them. If the file cannot be read as text for any reason, the script should fall back to reading the raw bytes and printing the first 1024 bytes instead. The script should run only when executed directly as the main program, and it should rely solely on the file path supplied at launch, with no other inputs, prompts, or configuration.
---"""

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
