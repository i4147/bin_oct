#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line JSON file sorter. It takes a path to a JSON file containing a top-level object (key-value mapping) and rewrites that same file with its entries reordered. By default, entries are ordered by the length of their keys, shortest first. An optional verbose flag switches the ordering criterion: entries are instead ordered by the number of items in their values when the value is a list, with non-list values treated as having zero items. The output must remain valid, human-readable JSON with two-space indentation, preserve non-ASCII characters without escaping, and be written back as UTF-8. The script should validate that its own output is parseable JSON before saving, and exit with a non-zero status code when no file path is provided. Focus on producing a clean, robust, and self-contained command-line tool with clear handling of the file-reading, sorting, and file-writing steps.
---"""

from __future__ import annotations
import json
from pathlib import Path
import sys
from typing import Any, Callable


def main() -> None:
    args = sys.argv[1:]
    verbose = False
    if args and args[0] == "-v":
        verbose = True
        args = args[1:]
    if not args:
        sys.exit(1)
    path: Path = Path(args[0])
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    key_func: Callable[[tuple[str, Any]], int]
    if verbose:
        key_func = lambda item: len(item[1]) if isinstance(item[1], list) else 0
    else:
        key_func = lambda item: len(item[0])
    sorted_data: dict[str, Any] = dict(sorted(data.items(), key=key_func))
    serialized: str = json.dumps(sorted_data, ensure_ascii=False, indent=2)
    json.loads(serialized)
    path.write_text(serialized, encoding="utf-8")


if __name__ == "__main__":
    main()
