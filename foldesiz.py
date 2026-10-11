#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that lets an AI coding agent recreate a Python script that organizes files into size-range folders. Describe the purpose, inputs, outputs, dependencies, logic, error handling, edge cases, and usage, without any code or snippets.

Create a Python 3 command-line script intended to run in a Termux environment on Android (the shebang points to the Termux Python interpreter). The script organizes files in the current working directory into subfolders grouped by file size.

**Purpose**
Recursively scan the current working directory, collect every regular file along with its size in bytes, and distribute those files into a set of folders whose names describe the size range they contain. Files are grouped so that each folder holds a roughly equal count of files, sorted by size.

**Dependencies**
- Use only the Python standard library, plus a local helper module named `dh` that the script imports. The `dh` module provides three functions that the script must call and that you should assume exist: `fsz(size_in_bytes)` returns a human-readable size string used in folder names; `should_skip(path)` returns True for paths that must be ignored (for example, the script's own folder or hidden/system entries); and `unique_path(path)` returns a non-colliding version of a destination path if the target already exists.
- Standard library modules to use: `__future__` annotations, `operator`, `os`, `shutil`, `sys`, and `pathlib.Path`.

**Behavior and logic**
1. Collect files: walk the working directory recursively (all depths). Skip any path for which `should_skip` returns True. Include only regular files (not directories or symlinks to directories). For each file, record its path and size, and return the list sorted ascending by size.
2. Determine folder count: if there are fewer than two files, use one folder. Otherwise compute the size range (max minus min). Target a range of one one-hundredth of the total range per folder, and derive the folder count as the integer quotient, with a minimum of 1, then cap it at the number of files. Handle the case where the range is zero (all files the same size) without dividing by zero: a zero range should yield a single folder.
3. Build range folders: sort the sizes and split them into the computed number of contiguous groups. Distribute files evenly: each group gets the floor of files divided by the group count, and the first `remainder` groups each receive one extra file. For each non-empty group, name the folder `<fsz(min)>-<fsz(max)>` using the group's minimum and maximum sizes, create it inside the working directory, and move the corresponding files into it using `shutil.move`. Use `unique_path` on each destination so existing files are not overwritten.
4. Ensure the script moves files rather than copying, and that it does not move files that are already inside a folder it has just created in a way that causes loops (files should be collected before any moves happen).
5. Output progress to standard output with concise messages (e.g., the number of files found, the number of folders to create, and each folder created with its file count). Use `sys.exit` with a non-zero code and a message to standard error for fatal conditions.

**Error handling and edge cases**
- No files found: print a message and exit cleanly with status 0.
- Single file or all files identical in size: create one folder.
- Files that cannot be stat'ed or moved (permission errors, files vanishing mid-run): catch `OSError`, report the path to standard error, and continue with the rest.
- Keyboard interrupt: exit gracefully with a message and status 130.
- Zero-byte files are valid and included.
- Ensure the script does not descend into or reprocess the folders it creates during the same run.

**Execution**
- Make the script executable with the Termux Python shebang line shown above.
- Run it from the directory whose contents should be organized; it takes no required arguments. Optionally, support a `--dry-run` flag that prints the planned folders and file counts without moving anything.
- Include a `main` guard so the functions can be imported without side effects.
- Use type hints where practical and keep the code readable with brief docstrings.

Deliver the complete script as a single file.
---"""

from __future__ import annotations

import operator
import os
import shutil
import sys
from pathlib import Path

from dh import fsz, should_skip, unique_path


def get_all_files(cwd: Path):
    files = []
    for path in cwd.rglob("*"):
        if should_skip(path):
            continue
        if path.is_file():
            size = path.stat().st_size
            files.append((path, size))
    return sorted(files, key=operator.itemgetter(1))


def get_num_folders(files) -> int:
    if len(files) < 2:
        return 1
    sizes = [size for _, size in files]
    max_size, min_size = (max(sizes), min(sizes))
    range_size = max_size - min_size
    target_range_per_folder = range_size / 100
    num_folders = max(1, int(range_size / target_range_per_folder))
    return min(num_folders, len(files))


def create_range_folders(cwd: Path, files, num_folders: int):
    sizes = sorted([size for _, size in files])
    folder_ranges = []
    files_per_folder = len(files) // num_folders
    remainder = len(files) % num_folders
    start_idx = 0
    for i in range(num_folders):
        end_idx = start_idx + files_per_folder + (1 if i < remainder else 0)
        folder_files = sizes[start_idx:end_idx]
        if folder_files:
            min_size, max_size = (min(folder_files), max(folder_files))
            folder_name = f"{fsz(min_size)}-{fsz(max_size)}"
            folder_ranges.append((min_size, max_size, folder_name))
            folder_path = os.path.join(cwd, folder_name)
            Path(folder_path).mkdir(exist_ok=True, parents=True)
        start_idx = end_idx
    return folder_ranges


def distribute_files(files, folders, cwd: Path) -> None:
    size_to_folder = {}
    for min_size, max_size, folder_name in folders:
        size_to_folder[min_size, max_size] = folder_name
    moved_count = 0
    for path, size in files:
        for (min_size, max_size), folder_name in size_to_folder.items():
            if min_size <= size <= max_size:
                dest_folder = os.path.join(cwd, folder_name)
                dest_path = os.path.join(dest_folder, Path(path).name)
                try:
                    dest_path = unique_path(dest_path)
                    shutil.move(path, dest_path)
                    moved_count += 1
                    break
                except Exception as e:
                    print(f"Failed to move {path}: {e}")
                break
        else:
            print(f"No folder match for {Path(path).name} ({size:,} bytes)")


def main() -> None:
    cwd = Path.cwd()
    files = get_all_files(cwd)
    if not files:
        print("No files found.")
        return
    num_folders = int(sys.argv[1]) if len(sys.argv) > 0 else get_num_folders(files)
    print(f"{num_folders} dirs will be created")
    folders = create_range_folders(cwd, files, num_folders)
    distribute_files(files, folders, cwd)
    print("Folderization complete!")


if __name__ == "__main__":
    raise SystemExit(main())
