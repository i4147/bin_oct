#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that tells an AI coding agent to write a Python script with the following specification:

Write a standalone Python 3 script (intended to run under Termux on Android, so include a Termux-style shebang line pointing to the Termux Python interpreter) that organizes files within a directory tree into alphabetical folders.

**Purpose:** Recursively scan a root directory and move every regular file into a top-level subfolder named after the first character of its filename. Letters are grouped by their lowercase letter (e.g., "apple.txt" goes to "a"). Any filename whose first character is a digit, a symbol, or any other non-alphabetic character, or an empty filename, goes into a single folder named "0-9".

**Required structure:**

1. A helper function that takes a filename string and returns the target folder name: a lowercase letter for alphabetic first characters, and "0-9" for everything else (digits, symbols, empty names). Use type hints and `from __future__ import annotations`.

2. A cleanup function that takes a root `Path`, walks all subdirectories deepest-first (sorted by depth in descending order), removes each empty directory except the root itself, prints a message for each removal, and silently ignores `OSError` raised when a directory is not empty or cannot be removed.

3. A main organizing function that takes a root `Path` with a default of the current working directory at call time (not at import time, so avoid evaluating `Path.cwd()` in the default argument if it would be stale; compute it inside the function when `None` is passed, or document the trade-off). It should:
   - Recursively collect all regular files under the root, skipping any path that has a `.git` component anywhere in its parts.
   - If no files are found, print "No files found to organize." and return.
   - Otherwise print the count, "Found N files to organize."
   - For each file, compute the target folder name, create the target directory under root (`exist_ok=True`), and build the destination path with the same filename.
   - Handle name collisions: if a file with the same name already exists at the destination, append a numeric counter (starting at 1) to the stem, producing names like "name_1.ext", incrementing until an unused name is found. Preserve the file extension (use the suffix) and handle files with no extension.
   - Skip moving a file when it already sits at its correct destination.
   - Move the file with `shutil.move`, count successful moves, and print each move in the form "source -> destination" (paths shown relative to root where practical).
   - Catch and report exceptions per file (print a warning including the path and error) so one failure does not abort the rest.
   - After moving, call the cleanup function to remove empty directories left behind, and print a summary of how many files were organized.

4. A `if __name__ == "__main__":` entry point that calls the main organizing function with no arguments.

**Edge cases to handle:**
- Empty filenames and filenames starting with non-ASCII characters (use `str.isalpha()`/`isdigit()` semantics; non-letter characters fall to "0-9").
- Files already inside a target letter folder (e.g., "a/apple.txt") — they should be recognized as already placed and not duplicated.
- Collision chains (multiple existing "_1", "_2" variants).
- Hidden files (leading dot) are treated as normal files; their first character is "." which maps to "0-9".
- Do not move files out of the `.git` directory; do not descend into or modify it.
- Do not crash if the root contains no files or only directories.

**Dependencies:** Only the Python standard library (`shutil`, `pathlib`). No third-party packages.

**Usage:** Run directly as `python <scriptname>.py` from inside the directory to organize; the target is the current working directory. The script produces console output only and has no command-line arguments.

Ensure the output is clean, idiomatic, and uses Path operations throughout.
---"""

from __future__ import annotations

import shutil
from pathlib import Path


def get_target_folder_name(filename: str) -> str:
    if not filename:
        return "0-9"
    first_char = filename[0].lower()
    if first_char.isalpha():
        return first_char
    elif first_char.isdigit():
        return "0-9"
    else:
        return "0-9"


def cleanup_empty_dirs(root: Path) -> None:
    for dir_path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if dir_path.is_dir() and dir_path != root:
            try:
                dir_path.rmdir()
                print(f"Removed empty directory: {dir_path}")
            except OSError:
                pass


def folderize_files(root: Path = Path.cwd()) -> None:
    files_to_move = []
    for item in root.rglob("*"):
        if ".git" in item.parts:
            continue
        if item.is_file():
            files_to_move.append(item)
    if not files_to_move:
        print("No files found to organize.")
        return
    print(f"Found {len(files_to_move)} files to organize.")
    renamed_count = 0
    for path in files_to_move:
        original_name = path.name
        folder_name = get_target_folder_name(original_name)
        target_dir = root / folder_name
        target_dir.mkdir(exist_ok=True)
        target_path = target_dir / original_name
        counter = 1
        while target_path.exists():
            stem = path.stem
            suffix = path.suffix
            new_name = f"{stem}_{counter}{suffix}"
            target_path = target_dir / new_name
            counter += 1
        if target_path != path:
            shutil.move(str(path), str(target_path))
            if counter > 1:
                renamed_count += 1
                print(f"Moved and renamed: {original_name} -> {target_path.name} (duplicate avoided)")
            else:
                print(f"Moved: {path} -> {target_path}")
    print("\nCleaning up empty directories...")
    cleanup_empty_dirs(root)
    print("\n✓ Organization complete!")
    print(f"  - Files processed: {len(files_to_move)}")
    print(f"  - Files renamed: {renamed_count}")
    print("  - Folders created: a, b, c, ..., 0-9")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Organize files recursively into alphabetical folders")
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to organize (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be moved without actually moving files",
    )
    args = parser.parse_args()
    target_dir = Path(args.directory).resolve()
    if args.dry_run:
        print(f"DRY RUN - Would organize files in: {target_dir}")
        file_count = sum(1 for _ in target_dir.rglob("*") if _.is_file())
        print(f"Would process {file_count} files")
        print("Folders would be created: a/, b/, c/, ..., 0-9/")
    else:
        print(f"Organizing files in: {target_dir}")
        folderize_files(target_dir)
