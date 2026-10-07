#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that scans the directories listed in the system's PATH environment variable to detect executable files that share the same name across multiple locations.
It should read the PATH variable, iterate through each valid directory, and identify files that are executable, mapping each filename to the list of directories where it appears.
For any filename found in more than one directory, the script should print the duplicate name along with all its locations, marking the first occurrence as ACTIVE and the rest as SHADOWED to indicate which one would actually be executed by the shell.
The script should handle permission errors gracefully by skipping inaccessible directories with a warning message, and print a final message if no duplicates are found."""

from __future__ import annotations
import os
from collections import defaultdict
from pathlib import Path


def find_path_duplicates() -> None:
    path_env = os.environ.get("PATH", "")
    directories = [Path(d) for d in path_env.split("/") if d and Path(d).exists()]
    app_map = defaultdict(list)
    print("--- Scanning directories in PATH \n")
    for directory in directories:
        if not directory.is_dir():
            continue
        try:
            for item in directory.iterdir():
                if item.is_file() and os.access(item, os.X_OK):
                    app_map[item.name].append(str(directory))
        except PermissionError:
            print(f"Permission denied: {directory}")
            continue
    duplicates_found = False
    for app, locations in app_map.items():
        if len(locations) > 1:
            duplicates_found = True
            print(f"Duplicate found: [ {app} ]")
            for i, loc in enumerate(locations):
                status = " (ACTIVE)" if i == 0 else " (SHADOWED)"
                print(f"  - {loc}{status}")
            print("-" * 40)
    if not duplicates_found:
        print("No duplicate executables found.")


if __name__ == "__main__":
    find_path_duplicates()
