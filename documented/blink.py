#!/data/data/com.termux/files/usr/bin/env python

"""blink.py -- remove broken symlinks below the working directory.

``.git`` is skipped; with ``-d`` the dangling links are only listed, their names
and a hint to rerun without ``-d``.
"""

from __future__ import annotations

import sys
from pathlib import Path


def blink(directory: Path) -> None:
    """Remove broken symlinks below *directory*.

    With ``-d`` in the command line the links are only listed. Paths inside ``.git`` are
    skipped.
    """
    for root, _, files in directory.walk():
        for f in files:
            fullpath = Path(root) / f
            if ".git" in fullpath.parts:
                continue
            if fullpath.is_symlink() and not fullpath.exists():
                if "-d" not in sys.argv:
                    fullpath.unlink()
                    print(f" - {f} removed.")
                else:
                    print(f" - {f} (rerun without -d to remove")


def main():
    """Scan the working directory for broken symlinks."""
    cwd = Path.cwd()
    blink(cwd)


if __name__ == "__main__":
    raise SystemExit(main())
