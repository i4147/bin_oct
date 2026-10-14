#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory recursively to find groups of duplicate files based on their content, and optionally removes the redundant copies. The tool should skip version-control metadata directories, ignore empty files and symbolic links, and only consider regular files. Content comparison should be performed efficiently, with hashing computed in parallel across many files to keep runtime low on large directory trees.
The script should accept a command-line flag that enables removal mode. When the flag is absent, the tool should run in a read-only reporting mode that lists each set of identical files, showing the paths grouped together and clearly indicating how many duplicates were found, or reporting that no duplicates exist. When removal mode is enabled, the tool should keep one file from each duplicate group (choosing a sensible, deterministic one) and delete the others, reporting every deletion it performs and handling errors such as permission problems or files that disappear mid-run gracefully without crashing the whole process.
The output should be human-readable,ise, and colorized or otherwise visually distinct for headings, duplicate groups, and warnings. Files that cannot be read should be skipped with a notice rather than halting execution. The script should be self-contained as a command-line utility that runs from the terminal, prints its results to standard output, and exits cleanly with an appropriate status code.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import cprint, mpf
from xorhash import get_xorhash

REMOVE = "-r" in sys.argv


def find_dups_optimized(root: Path):
    from os import walk as os_walk

    file_hashes = {}
    paths_to_process = []
    for r, _, files in os_walk(root):
        for file in files:
            path = Path(r) / file
            if ".git" in path.parts or not path.stat().st_size:
                continue
            if not path.is_symlink() and path.is_file() and path.exists():
                paths_to_process.append(path)
    if not paths_to_process:
        return {}
    results = mpf(get_xorhash, paths_to_process)
    for res in results:
        hash_result, path = res
        if hash_result is not None:
            file_hashes.setdefault(hash_result, []).append(path)
    return {h: paths for h, paths in file_hashes.items() if len(paths) > 1}


if __name__ == "__main__":
    cwd = Path.cwd()
    dupes = find_dups_optimized(cwd)
    if not dupes:
        print("No dups")
        sys.exit(1)
    for h, paths in dupes.items():
        cprint(f"dups with hash: {h}")
        for p in paths:
            print(" - ", p)
    if REMOVE:
        for paths in dupes.values():
            for p in paths[1:]:
                Path(p).unlink()
    print(f"Found {len(dupes)} group(s) of dups")
