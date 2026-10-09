#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that scans a fixed Termux site-packages directory (`/data/data/com.termux/files/home/.local/lib/python3.12/site-packages`) for all files named "METADATA" found recursively.
For each METADATA file, it reads and lowercases its content, then checks whether it contains the string "requires-dist: " followed by a dependency name passed as a command-line argument (sys.argv[1]).
If a match is found, it prints the name of the parent directory of that METADATA file, effectively identifying which installed packages declare the given package as a dependency.
"""

from __future__ import annotations
import sys
from pathlib import Path


def process_file(path: Path, text: str) -> None:
    path = Path(path)
    content = path.read_text().lower()
    target1 = "requires-dist: " + text
    if target1 in content:
        print(path.parent.name)


if __name__ == "__main__":
    cwd = Path("/data/data/com.termux/files/home/.local/lib/python3.12/site-packages")
    target = sys.argv[1]
    for path in cwd.rglob("METADATA"):
        process_file(path, target)
