#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans all `.py` files in the current directory (excluding itself), runs `black --check` on each to verify formatting compliance, and sorts them into two subfolders: `ok/` for files that pass the check and `error/` for files that fail.
It should create these directories if they don't exist, print progress messages showing the check result for each file, and avoid overwriting existing files at the destination by appending a numeric suffix (e.g., `_1`, `_2`) when a name collision occurs.
The script should exit with the return code of the `main()` function."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

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
