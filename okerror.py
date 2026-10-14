#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory for Python source files and sorts them into two folders based on whether they conform to the Black code formatter's style. The tool should ignore itself when scanning. For each candidate file, it should run a Black formatting check; files that pass are moved into an "ok" folder, and files that fail are moved into an "error" folder, creating either folder if it does not already exist. If a file with the same name already exists at the destination, the tool should preserve both by renaming the incoming file with an incrementing numeric suffix before its extension. While processing, it should print a clear progress message for each file showing the file being checked and where it was placed, using a check mark for passing files and a clear failure indicator for failing files. The tool should be a standalone, runnable command-line script that requires no arguments, and it should handle the case where Black is not installed or fails to run gracefully with a helpful message rather than crashing.
---"""

from __future__ import annotations
from pathlib import Path
import shutil
import subprocess

ERROR_DIR = Path("error")
OK_DIR = Path("ok")


def ensure_dirs() -> None:
    ERROR_DIR.mkdir(exist_ok=True)
    OK_DIR.mkdir(exist_ok=True)


def unique_destination(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    counter = 1
    while True:
        new_dest = parent / f"{stem}_{counter}{suffix}"
        if not new_dest.exists():
            return new_dest
        counter += 1


def black_check(path: Path) -> bool:
    result = subprocess.run(["black", "--check", str(path)], capture_output=True)
    return result.returncode == 0


def main() -> None:
    ensure_dirs()
    for py_file in Path().glob("*.py"):
        if py_file.name == Path(__file__).name:
            continue
        print(f"Checking {py_file}...")
        if black_check(py_file):
            dest = unique_destination(OK_DIR / py_file.name)
            print(f"  ✓ OK → {dest}")
        else:
            dest = unique_destination(ERROR_DIR / py_file.name)
            print(f"  ✗ ERROR → {dest}")
        shutil.move(str(py_file), str(dest))


if __name__ == "__main__":
    raise SystemExit(main())
