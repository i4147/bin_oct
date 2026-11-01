#!/data/data/com.termux/files/usr/bin/env python
"""pyco.py -- remove ``__pycache__`` directories.

The number of directories and the space freed are reported.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from dh import fsz, gsz


def clean_pycache(start_dir: Path = Path.cwd()) -> None:
    """Delete every ``__pycache__`` tree below *start_dir* and report the space
    freed."""
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
