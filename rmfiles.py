#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a plain-text list of file names from a file (defaulting to a file named "list.txt" in the current directory, but optionally accepting a different list file path from the command line), and deletes the files named in that list from the current working directory. The script should ignore blank lines and lines beginning with a comment marker. For each entry, it must only delete files that sit directly in the current working directory; any entry that points into a subdirectory or elsewhere on the filesystem must be skipped with a warning written to the error stream. For each file successfully removed, report the removal to standard output. If a listed file does not exist, report it as not found on the error stream and continue processing the remaining entries. If the list file itself does not exist, print a clear error message to the error stream and exit with a non-zero status code. After processing, if the list file itself resides in the current working directory, delete it as well. The script should exit with status zero on normal completion.
---"""

from __future__ import annotations
from pathlib import Path
import sys

DEFAULT_LIST = "list.txt"


def main() -> int:
    list_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LIST
    list_file = Path(list_name)
    if not list_file.is_file():
        print(f"Error: list file not found: {list_file}", file=sys.stderr)
        return 1
    cwd = Path.cwd()
    removed = 0
    missing = 0
    for raw_line in list_file.read_text().splitlines():
        name = raw_line.strip()
        if not name or name.startswith("#"):
            continue
        target = cwd / name
        if target.parent.resolve() != cwd.resolve():
            print(f"skipping (not top-level): {name}", file=sys.stderr)
            continue
        if target.is_file():
            target.unlink()
            print(f"removed: {name}")
            removed += 1
        else:
            print(f"not found: {name}", file=sys.stderr)
            missing += 1
    if list_file.resolve().parent == cwd.resolve():
        list_file.unlink()
        print(f"removed list file: {list_file.name}")
    print(f"\nDone. {removed} removed, {missing} not found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
