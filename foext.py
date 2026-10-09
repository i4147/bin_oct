#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that organizes files in the current working directory by moving each file into a subfolder named after its lowercase extension (files without an extension go into a folder called "no_extension").
It should iterate over all entries in the current directory, skip anything that isn't a regular file, create the destination folder if it doesn't already exist, and then move the file into that folder using shutil.move, preserving the original filename.
The script should run as a standalone executable module via a main() function invoked through the standard __main__ guard.
"""

from __future__ import annotations
import shutil
from pathlib import Path


def main() -> None:
    cwd = Path.cwd()
    for item in cwd.iterdir():
        if not item.is_file():
            continue
        ext = item.suffix.lower().lstrip(".") or "no_extension"
        target_dir = cwd / ext
        target_dir.mkdir(exist_ok=True)
        shutil.move(str(item), target_dir / item.name)


if __name__ == "__main__":
    raise SystemExit(main())
