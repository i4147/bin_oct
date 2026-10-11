#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script named collect_files.py, intended to run under Termux on Android (shebang pointing to the Termux Python path). Its purpose is to recursively find every file with a given extension under the current working directory and copy each one into a folder named after that extension, created inside the current directory, without ever overwriting existing files.

Requirements:

**Interface**
- Run as `python collect_files.py <extension>`, where the single argument is a file extension given without the leading dot (for example `pdf` or `jpg`).
- If the number of command-line arguments is not exactly one, print a usage line in the form `Usage: python collect_files.py <extension>` and exit with status code 1.
- Normalize the argument by stripping whitespace and any leading dot before use, so `.txt` and `txt` behave the same. Treat the extension case-sensitively as provided, relying on the filesystem's pattern matching.
- Use `from __future__ import annotations` for type-hint compatibility, and use only the standard library: `shutil`, `sys`, and `pathlib.Path`.

**Target folder**
- The destination folder is `<current working directory>/<extension>`. Create it with parents allowed and no error if it already exists.

**Discovery and copying**
- Search recursively from the current working directory for files matching the pattern `*.<extension>`.
- Process only regular files (skip directories and anything that is not a file).
- Skip any file that already resides inside the destination folder, so the script never copies its own output back into itself or re-processes files from previous runs.
- For each qualifying file, copy it with metadata preservation (equivalent to `shutil.copy2`) into the destination folder, keeping its original base filename.
- Name collisions must never overwrite: if the base filename already exists in the destination, try `<stem>_1<suffix>`, then `<stem>_2<suffix>`, and so on, incrementing until an unused name is found. Use the file's stem and suffix as separated by pathlib.
- Implement the unique-name logic as a separate helper function that takes the destination directory and filename and returns the chosen destination path.

**Output**
- For each successful copy, print a line in the form `Copied: <source path> -> <destination path>`.
- If copying a single file raises any exception, catch it, print `Error copying <source path>: <error>`, and continue with the remaining files without aborting.
- After the traversal, print a blank line followed by `Finished collecting files.`, then print `Total files copied: <count>` where the count includes only successful copies.

**Edge cases and behavior notes**
- If no matching files exist, the script still creates the empty folder and reports zero copied files.
- Files with the same name from different subdirectories are all preserved via the numeric suffix scheme.
- The script runs synchronously with no progress bar, confirmation prompts, or logging to files, and makes no network calls.
- Errors from directory creation (outside the per-file try block) are not specially handled and may propagate.

**Execution**
- Entry point is guarded by the standard `if __name__ == "__main__":` check, which performs argument validation and then runs the collection for the given extension.
---"""

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
