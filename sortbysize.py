#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans all top-level entries (files and directories) in a given root folder, skipping symbolic links.
For each entry, it computes the total size in bytes—recursively summing file sizes for directories (again skipping symlinks) or reading the file size directly for files—and stores the result as a dictionary with "name" and "size" keys.
The script sorts these entries in descending order by size and, when run directly, applies this to the current working directory, then writes the sorted list as indented JSON to a file named after the current directory (e.g., "foldername.json") in the current working directory."""

from __future__ import annotations

import json
import operator
from pathlib import Path


def sort_by_size(root_folder: Path):
    items = []
    for path in root_folder.glob("*"):
        if path.is_symlink():
            continue
        if path.is_dir():
            size = sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and (not p.is_symlink()))
        if path.is_file():
            size = path.stat().st_size
        items.append({"name": path.name, "size": size})
    items.sort(key=operator.itemgetter("size"), reverse=True)
    return items


if __name__ == "__main__":
    cwd = Path.cwd()
    data = sort_by_size(cwd)
    outfile = Path(cwd.name + ".json")
    with outfile.open("w", encoding="utf-8") as out:
        json.dump(data, out, indent=2)
