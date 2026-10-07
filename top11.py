#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that scans the current working directory recursively (using helper functions `get_files` and `fsz` from a local `dh` module) to find and display the largest files.
It should accept an optional command-line argument specifying how many top files to show, defaulting to 11 if not provided.
The script should collect each file's relative path and size, sort them by size in descending order, and print a formatted table with columns for rank number, truncated file path (capped at 80 characters, with a leading "..." if truncated), and human-readable file size.
If no files are found, it should print a message indicating so instead of the table."""

from __future__ import annotations
import operator
import sys
from pathlib import Path
from dh import fsz, get_files

cwd = Path.cwd()
N = int(sys.argv[1]) if len(sys.argv) > 1 else 11


def get_sizes() -> list[tuple[Path, int]]:
    return [(path.relative_to(cwd), path.stat().st_size) for path in get_files(cwd)]


def main() -> None:
    sizez = get_sizes()
    if not sizez:
        print("No files found or unable to access directory.")
        return
    sizez.sort(key=operator.itemgetter(1), reverse=True)
    num_files = N or 11
    top_files = sizez[:num_files]
    max_path_len = max((len(str(path)) for path, size in top_files))
    max_path_len = min(max_path_len, 80)
    print(f"{'No.':<4} {'File Path':<{max_path_len}} {'Size':>12}")
    print("-" * (max_path_len + 20))
    for i, (path, size) in enumerate(top_files, 1):
        path_str = str(path)
        if len(path_str) > max_path_len:
            path_str = "..." + path_str[-(max_path_len - 3) :]
        size_str = fsz(size)
        print(f"{i:<3} {path_str[: max_path_len - 3]:<{max_path_len}} {size_str:>12}")


if __name__ == "__main__":
    raise SystemExit(main())
