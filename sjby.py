#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that reads a JSON file path from the command line arguments and loads its top-level object into memory.
Support an optional "-v" flag placed before the path: without it, sort the object's keys by the length of the key string; with it, sort keys by the length of the value when the value is a list (treating non-list values as length 0).
Rebuild the dictionary in the resulting sorted order, serialize it back to JSON with an indent of 2 and non-ASCII characters preserved, validate the serialized string by parsing it again, and then overwrite the original file with this formatted, sorted JSON.
If no file path argument is provided, the script should exit with a non-zero status code."""

from __future__ import annotations
import json
import sys
from pathlib import Path
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
