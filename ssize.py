#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that lists the entries of a directory (by default, the current working directory), skipping symbolic links, and calculates the size of each entry, including the total size of all listed entries combined. The script should display the results in ascending order of size, with the smallest item first, and show each entry's name alongside its human-readable size. Each size should be presented in a readable unit (such as bytes, KB, MB, or GB), and the script should print the cumulative total size at the end. Use colored, styled terminal output to make the names, sizes, and total visually distinct. The script should run as a standalone command-line tool with no required arguments, and it should rely on helper functions for computing and formatting sizes so that the core logic remains focused on gathering, sorting, and displaying the directory contents.
---"""

from __future__ import annotations
import operator
from pathlib import Path
from dh import fsz, gsz

total = 0


def list_and_sort_by_size(path: Path = Path()):
    items = []
    global total
    for p in path.glob("*"):
        if p.is_symlink():
            continue
        size = gsz(p)
        total += size
        items.append({"name": p.name, "size": size})
    items.sort(key=operator.itemgetter("size"), reverse=False)
    return items


if __name__ == "__main__":
    data = list_and_sort_by_size()
    for k in data:
        print(f"{k['name']} : \x1b[5;96m {fsz(k['size'])}\x1b[0m")
    print(f"\ntotal:\x1b[5;94m {fsz(total)}\x1b[0m")
