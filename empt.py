#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
from pathlib import Path
import sys

if __name__ == "__main__":
    Path(sys.argv[1].strip()).write_text("")
