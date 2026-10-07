#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that moves a file or directory given as the first command-line argument into a fixed "repos" folder under the user's home directory.
It should resolve the source path, compute the destination path by combining the repos directory with the source's base name, and if a file or folder with that name already exists at the destination, generate a unique alternative name using a helper function called unique_path imported from a local module named dh.
The script then performs the move using shutil.move and prints a message showing the original name and the final destination name in the format "source --> destination"."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path
from dh import unique_path

if __name__ == "__main__":
    src = Path(sys.argv[1]).resolve()
    cwd = Path.home() / "repos"
    dst = cwd / src.name
    if dst.exists():
        dst = unique_path(dst)
    shutil.move(str(src), str(dst))
    print(f"{src.name} --> {dst.name}")
