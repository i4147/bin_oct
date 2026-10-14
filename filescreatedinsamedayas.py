#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path as a command-line argument and reports the date that file was created, then lists all other files in the same directory that were created on that same calendar date.
The tool should:
- Accept exactly one command-line argument, the path to a target file. If the argument count is wrong, print a brief usage message and exit with a non-zero status.
- Verify the target file exists. If it does not, print a clear error message and exit with a non-zero status.
- Determine the target file's date using a timestamp appropriate to the operating system: use the creation time on Windows, and the most reliable available modification-based timestamp on other platforms. Handle any errors gracefully and report them to the user.
- Print a header showing the input file name and its date, followed by a visual separator.
- Scan the target file's containing directory (non-recursively) and check each entry. Only consider regular files; skip subdirectories and entries that cannot be accessed. Compare each file's timestamp date against the target's date.
- Output the names of all matching files (including the target itself, if appropriate) in a clear, readable list, sorted alphabetically, along with a count of matches.
- Handle a file in the current working directory (no parent folder specified) correctly.
- Fail safely on permission errors or unreadable entries without crashing the whole run, continuing to process the remaining files.
- Keep output concise, human-readable, and free of stack traces during normal error conditions.
---"""

from __future__ import annotations
from datetime import datetime
import os
from pathlib import Path
import sys


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
