#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that scans the current working directory and its subdirectories to find Python scripts lacking a file extension.
It should use helper functions from a module named "dh" (get_filez, is_binary, is_python_file, should_skip) to enumerate files, skip irrelevant or binary entries, and identify files that start with a shebang line ("#!") and are recognized as Python files.
The script defines a helper to check for a shebang by reading the first two bytes of a file, and a main function that collects matching extensionless Python scripts into a list.
When run directly, it prints the relative paths (relative to the current directory) of all found scripts, or a message indicating none were found if the list is empty."""

from __future__ import annotations
from pathlib import Path
from dh import get_filez, is_binary, is_python_file, should_skip


def has_shebang(path):
    with path.open("rb") as f:
        first_two = f.read(2)
        if first_two == b"#!":
            return True
    return False


def find_scripts_without_extension(directory: Path):
    swe = []
    for item in get_filez(directory):
        if should_skip(item):
            continue
        if item.is_file() and (not item.suffix):
            if is_binary(item):
                continue
            if has_shebang(item) and is_python_file(item):
                swe.append(item)
    return swe


if __name__ == "__main__":
    cwd = Path.cwd()
    found_scripts = find_scripts_without_extension(cwd)
    if found_scripts:
        print("Found Python scripts without extension (relative paths):")
        for script_path in found_scripts:
            print(script_path.relative_to(cwd))
    else:
        print("No Python scripts without extension found in the current directory or its subdirectories.")
