#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with the following specification:

Create a standalone Python command-line script (Termux-compatible, with a `/data/data/com.termux/files/usr/bin/env python` shebang line and `from __future__ import annotations` at the top) that scans a directory for Python wheel files (`.whl`) and moves those that contain no usable code into a subdirectory.

**Purpose:** Identify "empty" wheels — wheel archives that contain no Python modules and no other code-bearing files — and relocate them into a separate folder so they can be reviewed or removed.

**Inputs:**
- A source directory path (provided on the command line via `argparse`), which is the directory to scan.
- An optional destination subdirectory name, defaulting to `empty_wheels`, created inside the source directory.
- Only top-level `*.whl` files in the source directory are considered (non-recursive glob).

**Outputs:**
- A destination folder (created with `exist_ok=True` semantics, so reruns don't fail) containing the wheels classified as empty.
- Console messages reporting: how many wheel files were found, the file currently being checked, which wheels were identified as empty and moved, which were kept, and a summary count. If no `.whl` files are found, print a message naming the source directory and return without error.

**Classification logic (`is_empty_wheel`):**
- Open the wheel as a zip archive and list all entry names.
- A wheel is **not empty** if any entry ends with `.py`, or if any entry is a "code-like" file: an entry that does not start with `dist-info/` or `__pycache__/`, does not end with `/` (directory entries), and does not end with `.dist-info/`.
- Otherwise the wheel is considered empty (returns `True`).
- Error handling: on `zipfile.BadZipFile`, print an error stating the file is not a valid zip and treat it as **not empty** (return `False`, so it is kept in place). On any other exception, print an error including the exception text and return `False`.

**Move logic:**
- Use `shutil.move` to relocate each empty wheel into the destination folder.
- Wheels classified as valid/non-empty remain untouched in the source directory.
- Track two lists (empty and valid) and report their counts at the end.

**Edge cases to handle:**
- No `.whl` files present.
- Corrupt or non-zip files with a `.whl` extension.
- Unreadable files or permission problems.
- Destination folder already exists.
- Wheels whose entries are only metadata (`.dist-info`) or cache directories — these count as empty.
- Filenames printed via their `.name` attribute.

**Usage:** Run as `python <script> <source_dir> [dest_name]` from the command line; the entry point should be guarded by `if __name__ == "__main__":` and use `argparse` to parse arguments. Use type hints (`Path`, `-> bool`, `-> None`) consistent with the original style, and standard library only (`argparse`, `shutil`, `zipfile`, `pathlib`).
---"""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path


def is_empty_wheel(wheel_path: Path) -> bool:
    try:
        with zipfile.ZipFile(wheel_path, "r") as zip_ref:
            all_files = zip_ref.namelist()
            has_py_files = any(file.endswith(".py") for file in all_files)
            has_code_dirs = any(
                not (file.startswith(("dist-info/", "__pycache__/")))
                and not file.endswith("/")
                and not file.endswith(".dist-info/")
                for file in all_files
            )
            return not (has_py_files or has_code_dirs)
    except zipfile.BadZipFile:
        print(f"Error: {wheel_path} is not a valid zip file")
        return False
    except Exception as e:
        print(f"Error reading {wheel_path}: {e}")
        return False


def move_empty_wheels(source_dir, dest_dir_name: str = "empty_wheels") -> None:
    source_path = Path(source_dir)
    dest_path = source_path / dest_dir_name
    dest_path.mkdir(exist_ok=True)
    wheel_files = list(source_path.glob("*.whl"))
    if not wheel_files:
        print(f"No .whl files found in {source_dir}")
        return
    print(f"Found {len(wheel_files)} wheel files to check")
    empty_wheels = []
    valid_wheels = []
    for wheel_file in wheel_files:
        print(f"Checking {wheel_file.name}...", end=" ")
        if is_empty_wheel(wheel_file):
            print("EMPTY")
            empty_wheels.append(wheel_file)
        else:
            print("OK")
            valid_wheels.append(wheel_file)
    if not empty_wheels:
        print("\nNo empty wheels found!")
        return
    print(f"\nFound {len(empty_wheels)} empty wheel(s)")
    for wheel_file in empty_wheels:
        dest_file = dest_path / wheel_file.name
        if dest_file.exists():
            counter = 1
            while dest_file.exists():
                dest_file = dest_path / f"{wheel_file.stem}_{counter}{wheel_file.suffix}"
                counter += 1
        shutil.move(str(wheel_file), str(dest_file))
        print(f"Moved: {wheel_file.name} -> {dest_dir_name}/{dest_file.name}")
    print("\nSummary:")
    print(f"  - Empty wheels moved to: {dest_dir_name}/")
    print(f"  - Valid wheels remaining: {len(valid_wheels)}")
    print(f"  - Total checked: {len(wheel_files)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Move empty .whl files (only dist-info, no Python code) to a subdirectory"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing .whl files (default: current directory)",
    )
    parser.add_argument(
        "-d",
        "--dest",
        default="empty_wheels",
        help="Destination subdirectory name (default: 'empty_wheels')",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()
    directory_path = Path(args.directory)
    if not directory_path.exists():
        print(f"Error: Directory '{args.directory}' does not exist")
        return
    move_empty_wheels(args.directory, args.dest)


if __name__ == "__main__":
    raise SystemExit(main())
