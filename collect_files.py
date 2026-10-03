#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that recursively searches the current working directory for all files matching a given extension (passed as a single command-line argument) and copies them into a newly created subfolder named after that extension, skipping files already inside the destination folder to avoid recursion.
The script should resolve filename collisions by appending an incrementing numeric suffix to the file stem before copying, using shutil.copy2 to preserve metadata.
It should print each copy operation as it happens, catch and report per-file copy errors without stopping, and finally print a summary with the total number of files copied.
If the extension argument is missing or the wrong number of arguments is supplied, it should print a usage message and exit with a non-zero status."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def unique_destination_path(dest_dir: Path, filename: str) -> Path:
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def collect_files_by_extension(extension: str) -> None:
    cwd = Path.cwd()
    target_dir = cwd / extension
    target_dir.mkdir(parents=True, exist_ok=True)
    copied_count = 0
    for path in cwd.rglob(f"*.{extension}"):
        if path.is_file() and target_dir not in path.parents:
            try:
                destination_path = unique_destination_path(target_dir, path.name)
                shutil.copy2(path, destination_path)
                print(f"Copied: {path} -> {destination_path}")
                copied_count += 1
            except Exception as e:
                print(f"Error copying {path}: {e}")
    print("\nFinished collecting files.")
    print(f"Total files copied: {copied_count}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python collect_files.py <extension>")
        sys.exit(1)
    file_extension = sys.argv[1].lower().strip(".")
    collect_files_by_extension(file_extension)
