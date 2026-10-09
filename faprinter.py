#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that reads a text file whose path is provided as the first command-line argument, streaming its lines one at a time using a generator function.
For each line, pass it through the `faprint` function imported from the `faprint` module, and print the returned result to standard output.
The script should process the file lazily line-by-line rather than loading it all into memory at once, and assumes the file is UTF-8 encoded.
"""

from __future__ import annotations
import sys
from pathlib import Path
from faprint import faprint as pp


def ylines(path: Path):
    with path.open(encoding="utf-8") as f:
        yield from f


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    for k in ylines(fn):
        print(pp(k))
