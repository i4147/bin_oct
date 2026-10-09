#!/data/data/com.termux/files/usr/bin/env python

from __future__ import annotations
import sys
from pathlib import Path

if __name__ == "__main__":
    Path(sys.argv[1].strip()).write_text("")
