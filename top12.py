#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree recursively, starting from the current working directory by default (with the option to specify a different root directory), and identifies the 10 largest regular files by size in bytes. The script should handle large directory trees efficiently without storing every file in memory, skip entries that are not regular files, and gracefully ignore files that cannot be accessed due to permission or other OS-level errors. When finished, it should output the results sorted from largest to smallest, with each line showing the file size in bytes followed by the file's path, and it should run this report when executed directly from the command line.
---"""

from __future__ import annotations
import heapq
import os
from pathlib import Path


def get_top_10_largest_files_optimized(directory: str = "."):
    top_10 = []
    for root, _dirs, files in os.walk(directory):
        for file in files:
            path = Path(root) / file
            if path.is_file():
                try:
                    size = path.stat().st_size
                    if len(top_10) < 10:
                        heapq.heappush(top_10, (size, path))
                    elif size > top_10[0][0]:
                        heapq.heapreplace(top_10, (size, path))
                except OSError:
                    pass
    return sorted(top_10, reverse=True)


if __name__ == "__main__":
    top_10 = get_top_10_largest_files_optimized()
    for size, path in top_10:
        print(f"{size} bytes - {path}")
