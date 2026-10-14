#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path as a command-line argument, strips any leading or trailing whitespace from that path, and creates an empty file at that location (overwriting it if it already exists). The script should run only when executed directly, not when imported as a module. It should require no user interaction and produce no console output on success.
---"""

from __future__ import annotations
from pathlib import Path
import sys

if __name__ == "__main__":
    Path(sys.argv[1].strip()).write_text("")
