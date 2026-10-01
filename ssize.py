#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans entries in a given directory (defaulting to the current directory), skipping symbolic links, and computes each item's size using a helper `gsz` function along with a human-readable formatter `fsz` from a local `dh` module.
It should collect each item's name and size into a list, sort the list ascending by size using `operator.itemgetter`, and accumulate a running total across all items via a global variable.
When run as the main script, it should print each item's name alongside its formatted size in blinking cyan ANSI color codes, then print the total size in blinking blue ANSI color codes."""

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
