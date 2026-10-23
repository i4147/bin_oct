#!/data/data/com.termux/files/usr/bin/python


from __future__ import annotations
from pathlib import Path
import shutil
import sys

from dh import unique_path


if __name__ == "__main__":
    src = Path(sys.argv[1]).resolve()
    cwd = Path.home() / "repos"
    dst = cwd / src.name
    if dst.exists():
        dst = unique_path(dst)
    shutil.move(str(src), str(dst))
    print(f"{src.name} --> {dst.name}")
