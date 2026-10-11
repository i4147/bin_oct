#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script that, given a single file path argument, reports the file's "creation" date and lists the other regular files in the same directory that share that same calendar date.

Requirements:

**Purpose and behavior**
- Accept exactly one command-line argument: the path to a target file.
- If the argument count is not exactly one, print a usage line in the form `Usage: python script.py <filename>` and exit with status 1.
- If the target path does not exist, print `Error: File '<filename>' does not exist.` and exit with status 1.
- Determine the target file's timestamp using a helper function that returns a `datetime` or `None`. On Windows (`sys.platform == "win32"`), use the status change time (`st_ctime`); on all other platforms (including Termux/Android), use the modification time (`st_mtime`). Convert with `datetime.fromtimestamp`. Wrap the stat call in a broad exception handler that prints `Error: <exception>` and returns `None`.
- If the timestamp cannot be obtained, exit with status 1.
- Extract the calendar date (`.date()`) of the target's timestamp.
- Print, in order:
  - `Input file: <filename>`
  - `Created on: <date>` (ISO format, e.g. YYYY-MM-DD)
  - a line of 40 hyphens
- Scan the target file's parent directory (use `"."` if the parent is empty). For each entry:
  - Build its full path by joining the directory and entry name.
  - Skip it if it is not a regular file, or if it is the same file as the target (use `samefile` comparison, not string comparison).
  - Obtain its timestamp with the same helper; if valid and its date equals the target date, record a tuple of (timestamp, filename).
- Sort the collected results ascending by timestamp (tuple sort), then print the matching files. (The output section after the "no matches" check should list each match with its timestamp and name; if none are found, print a short message indicating no other files share the same date.)
- Only the immediate directory is scanned; subdirectories are not recursed into.

**Notable details and edge cases**
- Use `from __future__ import annotations` for type hints such as `datetime | None`.
- Include a Termux-style shebang line (`/data/data/com.termux/files/usr/bin/env python`).
- Use only the Python standard library: `os`, `sys`, `datetime`, `pathlib`.
- Handle the case where the target's parent directory is the current directory.
- Files that disappear or cannot be stat'ed during the scan should be silently skipped (or reported via the helper's error print) without aborting the scan.
- Errors from the helper are printed but do not stop the overall loop.
- Use exit code 1 for all failure conditions and normal completion otherwise.

**Style**
- Keep the script short, readable, and organized into a `get_file_creation_time` function, a `main` function, and an `if __name__ == "__main__":` guard calling `main()`.
- Use f-strings for output and type annotations on function signatures.
---"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path


def get_file_creation_time(path: str) -> datetime | None:
    try:
        stat = os.stat(path)
        if sys.platform == "win32":
            return datetime.fromtimestamp(stat.st_ctime)
        return datetime.fromtimestamp(stat.st_mtime)
    except Exception as e:
        print(f"Error: {e}")
        return None


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]
    if not Path(filename).exists():
        print(f"Error: File '{filename}' does not exist.")
        sys.exit(1)
    directory = Path(filename).parent or "."
    target_time = get_file_creation_time(filename)
    if not target_time:
        sys.exit(1)
    target_date = target_time.date()
    print(f"Input file: {filename}")
    print(f"Created on: {target_date}")
    print("-" * 40)
    found_files = []
    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        if not Path(path).is_file() or Path(path).samefile(filename):
            continue
        file_time = get_file_creation_time(path)
        if file_time and file_time.date() == target_date:
            found_files.append((file_time, file))
    found_files.sort()
    if not found_files:
        print("No other files found created on the same day.")
    else:
        print(f"Found {len(found_files)} other file(s) created on the same day:")
        for file_time, file in found_files:
            print(f"{file_time.strftime('%H:%M:%S')} - {file}")


if __name__ == "__main__":
    raise SystemExit(main())
