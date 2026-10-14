#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a starting directory (defaulting to the current working directory when run directly) for all Python cache folders, deletes each one along with its contents, and reports how many were removed and the total disk space freed. The script should measure the size of each cache folder before deletion, sum these sizes, and present the total in a human-readable format (such as bytes, KB, MB, or GB). It should skip or safely handle any cache folder that no longer exists by the time it is processed. If no cache folders are found, it should print a short message indicating that nothing was found. Output should be concise, using a clear bulleted summary of the total space freed and the number of folders removed. The script should be runnable from the command line and designed so that its cleanup function can also be called and reused with a custom directory path.
---"""

from __future__ import annotations
from pathlib import Path
import shutil
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
