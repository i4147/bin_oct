#!/data/data/com.termux/files/usr/bin/python
import sys
from pathlib import Path

if __name__ == "__main__":
    fn = Path(sys.argv[1])
    new_stem = sys.argv[2]

    new_name = new_stem + ".cpython-314-arm-linux-androideabi.so"
    new_path = fn.with_name(new_name)
    fn.rename(new_path)
