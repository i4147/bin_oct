#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that flattens a directory tree by moving every file found in its subdirectories up into a single chosen root folder. The script should accept a directory path (defaulting to the current working directory), validate that it exists and is a directory, and report a clear error if it does not. It should recursively discover all files beneath the root, skipping any that already sit directly in the root, and print a summary at the start showing the resolved root path and the number of files to be moved.
When moving a file would collide with an existing file of the same name in the root, the script must never overwrite existing data. Instead, it should generate a unique alternative filename by appending an incrementing numeric suffix before the file extension, repeating until a free name is found, and it should count how many files were renamed this way.
After all files are moved, the script should remove any subdirectories that have become empty as a result, cleaning up the tree while leaving the root itself intact. It should handle errors gracefully on individual files (for example permission problems or files that vanish mid-operation) by reporting the problem and continuing with the remaining files rather than crashing. Finally, it should print a concise completion report stating how many files were moved, how many were renamed to avoid conflicts, and any errors encountered. The script should be runnable from the command line, optionally taking the target directory as an argument, and should provide informative console output throughout the process.
---"""

from __future__ import annotations
from pathlib import Path
import shutil
import sys


def unique_target(target: Path) -> Path:
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    parent = target.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def flatten_directory(directory="."):
    root = Path(directory).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a valid directory")
        return
    print(f"Flattening directory: {root}")
    files_to_move = [path for path in root.rglob("*") if path.is_file()]
    if not files_to_move:
        print("No files found in subdirectories.")
        return
    print(f"Found {len(files_to_move)} file(s) to move")
    moved_count = 0
    renamed_count = 0
    for path in files_to_move:
        target_path = root / path.name
        if target_path == path:
            continue
        if target_path.exists():
            new_target = unique_target(target_path)
            print(f"Renaming: {path.name} -> {new_target.name} (name already taken)")
            target_path = new_target
            renamed_count += 1
        try:
            shutil.move(str(path), str(target_path))
            print(f"Moved: {path} -> {target_path}")
            moved_count += 1
        except Exception as e:
            print(f"Error moving {path}: {e}")
    print(f"\nMoved {moved_count} file(s), {renamed_count} renamed due to collisions")
    all_dirs = sorted(
        (p for p in root.rglob("*") if p.is_dir()),
        key=lambda p: len(p.parts),
        reverse=True,
    )
    removed_dirs = 0
    for subdir in all_dirs:
        try:
            if not any(subdir.iterdir()):
                subdir.rmdir()
                print(f"Removed empty directory: {subdir}")
                removed_dirs += 1
        except Exception as e:
            print(f"Error removing {subdir}: {e}")
    print(f"\nRemoved {removed_dirs} empty directory(ies)")
    print("Flattening complete!")


def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    flatten_directory(target_dir)


if __name__ == "__main__":
    main()
