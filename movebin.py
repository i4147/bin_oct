#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory, identifies all binary files directly within it (ignoring subdirectories), and moves them into a subfolder named "binary" created in that same directory if it does not already exist. For each file moved, the script should report the original filename and its new location. a move fails for any file, it should report the filename and the reason, then continue processing the remaining files. When finished, it should print a summary: either a message indicating that no binary files were found, or the total count of binary files successfully moved. The script should run as a command-line tool and exit cleanly when complete.
---"""

from __future__ import annotations
from pathlib import Path
import shutil


def main() -> None:
    cwd = Path.cwd()
    binary_dir = cwd / "binary"
    binary_dir.mkdir(exist_ok=True)
    files_moved = 0
    for f in cwd.iterdir():
        if f.is_file() and is_binary(Path(f)):
            try:
                shutil.move(str(f), binary_dir / f.name)
                print(f"Moved: {f.name} -> binary/{f.name}")
                files_moved += 1
            except Exception as e:
                print(f"Failed to move {f.name}: {e}")
    if files_moved == 0:
        print("No binary files found to move.")
    else:
        print(f"Total binary files moved: {files_moved}")


if __name__ == "__main__":
    raise SystemExit(main())
