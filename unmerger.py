#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single merged text file as its command-line input, where the file contains multiple source files concatenated together, each introduced by a header line in the form "# File: <relative path>". The script should read the merged file, split it back into its individual files based on these headers, and recreate each file at its original relative path. Trim any leading blank lines and trailing whitespace from each extracted file's content so the output is clean.
Key behaviors:
- If no input file argument is provided, print a brief usage message and exit with a non-zero status.
- Handle the input file gracefully: if it cannot be read, report a clear error and exit with a non-zero status.
- Create any missing parent directories needed for each recovered file.
- Never silently overwrite existing files. If a target path already exists, generate a unique alternative name by appending an incrementing numeric suffix before the file extension (e.g., "name_1.ext", "name_2.ext") and write to that instead.
- Preserve the original relative directory structure and file names as much as possible.
- Write files using UTF-8 encoding and report to the user, for each file, the path it was written to.
- Handle edge cases such as empty input, headers with no following content, and duplicate headers within the same merged file.
- Provide a concise summary at the end indicating how many files were recovered.
The script should be a standalone, runnable tool with a clear entry point, suitable for use from the command line.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys


def parse_merged_file(path):
    with open(path, "r") as f:
        content = f.read()
    pattern = r"^# File: (.+?)$"
    parts = re.split(pattern, content, flags=re.MULTILINE)
    files = {}
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            path = parts[i].strip()
            file_content = parts[i + 1].lstrip("\n").rstrip()
            files[path] = file_content
    return files


def get_unique_path(path):
    path = Path(path)
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <input_file>")
        sys.exit(1)
    input_file = sys.argv[1]
    files = parse_merged_file(input_file)
    for path, file_content in files.items():
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        unique_path = get_unique_path(path)
        unique_path.write_text(file_content)
        status = "Renamed to" if unique_path.name != path.name else "Created"
        print(f"{status}: {unique_path}")


if __name__ == "__main__":
    raise SystemExit(main())
