#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python cleanup script for Termux's Python site-packages directory that detects the current Python version dynamically and locates the corresponding site-packages path under "/data/data/com.termux/files/usr/lib/pythonX.Y/site-packages".
For each subdirectory in that location containing exactly one item, it should print the directory name, and if the directory name contains "dist-info", check whether it holds a "top_level.txt" or "entry_points.txt" file; if so, print a cyan-colored message via a "cprint" function imported from a local "dh" module indicating the direct the entire directory using shutil.rmtree script should exit gracefully (doing nothing) if the target site-packages path does not exist, and should run its main logic when executed as a script, returning the result via SystemExit."""

from __future__ import annotations
from pathlib import Path
import shutil
import sys

from dh import cprint


major, minor, _, _, _ = sys.version_info
py_version = f"{major}.{minor}"


def process_dir(dr: Path) -> bool:
    print(dr.name)
    if "dist-info" in dr.name:
        for k in dr.iterdir():
            if k.name in {"top_level.txt", "entry_points.txt"}:
                cprint(f"{dr} removed", "cyan")
                shutil.rmtree(dr)
    return True


def main() -> None:
    cwd = Path(f"/data/data/com.termux/files/usr/lib/python{py_version}/site-packages")
    if not cwd.exists():
        return
    for path in cwd.iterdir():
        if path.is_dir() and len(list(path.iterdir())) == 1:
            process_dir(path)


if __name__ == "__main__":
    raise SystemExit(main())
