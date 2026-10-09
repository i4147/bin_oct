#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that recursively scans a given directory (defaulting to the current directory) and efficiently finds the 10 largest files using a min-heap to avoid storing all file sizes in memory.
It should walk the directory tree with os.walk, retrieve each file's size via Path.stat(), and gracefully skip files that raise OSError (e.g., broken symlinks or permission errors).
The function should return the top 10 files sorted in descending order by size as (size, path) tuples, and when run as a script, print each file's size in bytes alongside its path.
"""

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
