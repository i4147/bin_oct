#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script that groups the subdirectories of the current working directory into a fixed number of balanced folders, measuring each subdirectory's recursive file size and distributing them using a greedy size-balancing strategy. The prompt should specify:

Purpose: Organize the immediate subdirectories of the current directory into N balanced groups (N supplied as a command-line argument), so that the total size of each group is roughly equal, by moving each subdirectory into a newly created group folder.

Inputs:
- A required positive integer command-line argument specifying the number of parts/groups, parsed with argparse.
- The current working directory is the implicit input; no other files are read.

Outputs:
- Console output: the count of discovered subdirectories, a per-subdirectory size line in megabytes with two decimal places, and a final confirmation message after reorganization.
- Filesystem changes: creation of group folders named with a "group_" prefix followed by a 1-based index, and moving each subdirectory into the group folder assigned to it.

Required behavior and logic:
- Only consider immediate child directories of the current directory (not files, not nested directories); exclude any directory whose name already starts with "group_" so that re-runs do not regroup previous output.
- Compute each directory's total size by recursively walking all files beneath it (rglob), summing file sizes via stat, skipping files that raise PermissionError or FileNotFoundError, and tolerating errors at the top-level walk without crashing. Do not follow the sizes of symlinks as files beyond what is_file reports.
- Sort directories by size in descending order, then assign each to the group with the currently smallest accedy longest-processing-time bin packing).
- Create each group folder (with exist_ok-style behavior so existing folders are reused) and move each assigned subdirectory into it using shutil.move.
- If no subdirectories are found, print a message stating so and exit without changes.
- Handle edge cases: empty directories (size 0), name collisions when moving (decide and document behavior, e.g., skip or report on existing destination), permission errors during moves (report and continue), and a requested number of parts that is zero or negative (reject with an error message via argparse validation).

Execution details:
- Use only the Python standard library: os, shutil, pathlib, argparse.
- Include a shebang line for Termux on Android (/data/data/com.termux/files/usr/bin/env python).
- Provide a main entry point guarded by a __name__ check that parses arguments and calls the grouping function.
- Use type hints on function signatures and keep the script a single file with clear, minimal helper functions (one for directory size, one for the grouping logic).
- Print progress and sizes using f-strings with the size converted to megabytes (bytes divided by 1024 times 1024).

Produce a complete, runnable script that follows these specifications.
---"""

import argparse
import os
import shutil
from pathlib import Path


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
    parser.add_argument(
        "-n",
        "--parts",
        type=int,
        default=3,
        help="Number of parts/groups to create (default: 3)",
    )
    args = parser.parse_args()

    folderize_directories(args.parts)
