#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the immediate contents of the current working directory, measures the size of each entry, and saves a size-ranked inventory of those entries to a JSON file.
The script should:
- Look only at the top-level items in the directory it is run from (files and subdirectories), without following symbolic links.
- For each regular file, record its size in bytes.
- For each subdirectory, record the total size in bytes of all regular files found anywhere beneath it, again ignoring symbolic links.
- Produce a list where each entry contains the item's name and its size.
- Sort the list so the largest items appear first.
- Write the result to a JSON file named after the current directory (using the directory's own name with a `.json` extension), formatted with indentation and UTF-8 encoding.
- Run its main behavior only when executed directly as a standalone program, not when imported.
Keep the implementation simple, robust to ordinary filesystem content, and self-contained using only the Python standard library.
---"""

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
