#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
from pathlib import Path
import sys


def blink(directory: Path) -> None:
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
    cwd = Path.cwd()
    blink(cwd)


if __name__ == "__main__":
    raise SystemExit(main())
