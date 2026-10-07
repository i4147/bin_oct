#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that takes a file path as a command-line argument, loads the file's contents using pickle deserialization, and writes the resulting raw bytes to a new file sharing the same base name but with a ".raw" extension.
The script should also print the deserialized data to standard output for inspection.
It should use pathlib for path handling and read the input file in binary mode."""

from __future__ import annotations
import pickle as pkl
from pathlib import Path

if __name__ == "__main__":
    import sys

    fn = Path(sys.argv[1].strip())
    with fn.open("rb") as f:
        data = pkl.load(f)
    outf = fn.with_suffix(".raw")
    outf.write_bytes(data)
    print(data)
