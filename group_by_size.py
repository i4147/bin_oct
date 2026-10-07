#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python 3.12 command-line script designed to run in a Termux environment (using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that organizes subdirectories of the current working directory into a specified number of balanced-size "group" folders.

The script's purpose is to help distribute many subdirectories into N groups (e.g., for balanced storage, archiving, or splitting data across drives/uploads) such that the total size of each group is as evenly balanced as possible, using a greedy bin-packing approach based on directory size.

Main behavior and requirements:

1. **Command-line interface**: Use `argparse` to accept a required argument specifying the number of groups/parts (`n_parts`) to split the subdirectories into (e.g., via a positional or `-n`/`--parts` argument).

2. **Directory size calculation**: Implement a helper function `get_direct` that recursively walks a directory (usingums the size bytes of all files within it, and gracefully handles `PermissionError` and `FileNotFoundError` by skipping inaccessible files/directories without crashing.

3. **Subdirectory discovery**: Scan the current directory (`.`) for immediate subdirectories, excluding any directories whose names already start with `group_` (so re-running the script doesn't include previously created group If no subdirectories are found, print a message and exit gracefully.

4. **Size reporting**: For each disc calculate and print its sizeabytes (formal places) in` - ribution algorithm**: Sort subdirectoriesbins" each and listories; for each directory (largest first), assignently having the smallest total size, and that bin's size.

6. **Groupder creation and moving**: For each bin, create a folder named `group_1`, `group_2`, ..., `group_N` in the current directory (using `mkdir(exist_ok=True)`), print a header showing the group name and its total size in MB, then move each assigned subdirectory into that group folder (e.g., using `shutil.move`), printing progress for each moved item.

7. **Output**: The script should print informative progress messages throughout — number of subdirectories found, individual directory sizes, group headers with total sizes, and confirmation of each directory being moved — so the user can follow the grouping and moving process in the terminal.

8. Use `pathlib.Path` for all filesystem path operations, and import `os`, `shutil`, `Path` from `pathlib`, and `argparse` at the top of the script. Wrap the main logic in a function (e.g., `folderize_directories(n_parts: int)`) and call it from a `if __name__ == "__main__":` block after parsing arguments.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/26HV6fb987beusRwxWie6K"""

import os
import shutil
from pathlib import Path
import argparse


def get_directory_size(path: Path) -> int:
    total_size = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total_size += entry.stat().st_size
                except (PermissionError, FileNotFoundError):
                    continue
    except (PermissionError, FileNotFoundError):
        pass
    return total_size


def folderize_directories(n_parts: int):
    current_dir = Path(".")

    subdirs = [p for p in current_dir.iterdir() if p.is_dir() and not p.name.startswith("group_")]

    if not subdirs:
        print("No subdirectories found in the current directory.")
        return

    print(f"Found {len(subdirs)} subdirectories. Calculating sizes...")

    dir_sizes = {}
    for subdir in subdirs:
        size = get_directory_size(subdir)
        dir_sizes[subdir] = size
        print(f" - {subdir.name}: {size / (1024 * 1024):.2f} MB")

    sorted_subdirs = sorted(subdirs, key=lambda x: dir_sizes[x], reverse=True)

    bins = [{"size": 0, "items": []} for _ in range(n_parts)]

    for subdir in sorted_subdirs:
        min_bin = min(bins, key=lambda b: b["size"])
        min_bin["items"].append(subdir)
        min_bin["size"] += dir_sizes[subdir]

    for i, b in enumerate(bins, start=1):
        group_name = f"group_{i}"
        group_path = current_dir / group_name
        group_path.mkdir(exist_ok=True)

        print(f"\n--- {group_name} (Total Size: {b['size'] / (1024 * 1024):.2f} MB) ---")

        for subdir in b["items"]:
            dest_path = group_path / subdir.name
            print(f"Moving '{subdir.name}' -> '{group_name}/'")
            shutil.move(str(subdir), str(dest_path))

    print("\nFolderization complete successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Group top-level subdirectories into N parts by similar size.")
    parser.add_argument("-n", "--parts", type=int, default=3, help="Number of parts/groups to create (default: 3)")
    args = parser.parse_args()

    folderize_directories(args.parts)
