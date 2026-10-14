#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory recursively, finds all files, and reports the largest ones in a neatly formatted table. The script should accept an optional command-line argument specifying how many files to list (defaulting to 11 if omitted or invalid). For each file, it should record its path relative to the working directory and its size in bytes. Files should be ranked from largest to smallest, and the top N entries displayed as a numbered table with columns for rank, file path, and human-readable size (such as KB, MB, or GB). Long file paths should be truncated sensibly so the table stays aligned and readable, with the path width capped at a reasonable maximum. If no files are found or the directory cannot be accessed, the script should print a clear message and exit gracefully without a traceback.
---"""

from __future__ import annotations
import operator
from pathlib import Path
import sys
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
