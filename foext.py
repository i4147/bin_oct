#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that organizes the files in the current working directory by their file type. The script should scan only the top-level files in the directory it is run from, ignoring subdirectories. For each file, determine its extension (case-insensitive, without the leading dot) and move the file into a subfolder named after that extension, creating the subfolder if it does not already exist. Files without any extension should be placed into a single designated folder for extensionless files. The script should not descend into existing subfolders, should not alter file contents or names, and should handle the move operation safely so that the original file is relocated rather than copied. The script should run as a standalone command-line tool that performs the reorganization in one pass without requiring user input, and it should exit cleanly with a successful status code when finished.
---"""

from __future__ import annotations
from pathlib import Path
import shutil


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
