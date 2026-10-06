#!/data/data/com.termux/files/usr/bin/python3.12
import os
import shutil
from pathlib import Path
import argparse


def get_directory_size(path: Path) -> int:
    """Calculate the total size of a directory in bytes recursively."""
    total_size = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total_size += entry.stat().st_size
                except (PermissionError, FileNotFoundError):
                    # Skip files that cannot be accessed due to permissions
                    continue
    except (PermissionError, FileNotFoundError):
        pass
    return total_size


def folderize_directories(n_parts: int):
    current_dir = Path(".")

    # Get all top-level subdirectories (excluding any existing 'group_' folders to avoid nesting loops)
    subdirs = [p for p in current_dir.iterdir() if p.is_dir() and not p.name.startswith("group_")]

    if not subdirs:
        print("No subdirectories found in the current directory.")
        return

    print(f"Found {len(subdirs)} subdirectories. Calculating sizes...")

    # Calculate sizes for each directory
    dir_sizes = {}
    for subdir in subdirs:
        size = get_directory_size(subdir)
        dir_sizes[subdir] = size
        print(f" - {subdir.name}: {size / (1024 * 1024):.2f} MB")

    # Sort subdirectories by size in descending order (Greedy LPT algorithm for balanced bin packing)
    sorted_subdirs = sorted(subdirs, key=lambda x: dir_sizes[x], reverse=True)

    # Initialize N bins
    bins = [{"size": 0, "items": []} for _ in range(n_parts)]

    # Distribute each directory into the bin with the smallest current total size
    for subdir in sorted_subdirs:
        min_bin = min(bins, key=lambda b: b["size"])
        min_bin["items"].append(subdir)
        min_bin["size"] += dir_sizes[subdir]

    # Create group directories and move the subdirectories
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
