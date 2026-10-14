#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path as a command-line argument, loads a serialized Python object from that file, and writes its raw binary contents to a new file in the same directory that shares the original file's base name but uses a ".raw" extension. The script should accept the path as input, strip any surrounding whitespace from it, verify that the input file can be read as a serialized object, save the extracted data as raw bytes, and print the loaded object to the console so the user can inspect it. It should be designed to run as a standalone command-line tool, with clear handling of cases where the input path is missing or the file cannot be loaded.
---"""

from __future__ import annotations
from pathlib import Path
import pickle as pkl

if __name__ == "__main__":
    import sys

    fn = Path(sys.argv[1].strip())
    with fn.open("rb") as f:
        data = pkl.load(f)
    outf = fn.with_suffix(".raw")
    outf.write_bytes(data)
    print(data)
