#!/data/data/com.termux/files/usr/bin/python
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
