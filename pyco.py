#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively searches a given starting directory (defaulting to the current working directory) for all `__pycache__` folders and deletes them using `shutil.rmtree`.
Before removing each folder, it should calculate its size using a helper `gsz` function and accumulate the total bytes freed and the count of directories removed.
After processing, it should print a formatted summary showing the total size freed (using a helper `fsz` function to format bytes) and the number of directories removed, or print a message indicating nothing was found if no `__pycache__` directories exist.
The size/formatting helper functions `gsz` and `fsz` should be imported from a local module named `dh`, and the script should run the cleanup on the current directory when executed as the main program."""

import shutil
from pathlib import Path
from dh import fsz, gsz


def clean_pycache(start_dir: Path = Path.cwd()) -> None:
    removed = 0
    sz = 0
    for path in start_dir.rglob("__pycache__"):
        if path.exists():
            sz += gsz(path)
            removed += 1
            shutil.rmtree(str(path))
    if removed:
        print(f"   • Total size freed: {fsz(sz)}")
        print(f"   • dirs removed: {removed}")
    else:
        print("nothing found.")


if __name__ == "__main__":
    cwd = Path.cwd()
    clean_pycache(cwd)
