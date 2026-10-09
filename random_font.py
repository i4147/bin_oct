#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that randomly selects a Termux font from WOFF2 files stored in "/sdcard/font", excluding italic variants and files smaller than 400KB, using the secrets module for random selection.
It should print the chosen index, total candidate count, and filename, then look for a corresponding .ttf file with the same base name and rename it to "~/.termux/font.ttf", removing any existing destination file first.
Include a helper function using fontTools' woff2.decompress to convert a WOFF2 file to TTF, silently ignoring any conversion errors.
The script should be runnable as a standalone module with a main entry point."""

from __future__ import annotations
from pathlib import Path
import secrets
import sys


def convert_with_fonttools(src, dst):
    from fontTools.ttLib import woff2

    try:
        woff2.decompress(src, dst)
    except Exception as e:
        return


def main():
    source_dir = Path("/sdcard/font")
    dst = Path.home() / ".termux" / "font.ttf"
    if dst.exists():
        dst.unlink()
    files = [p for p in source_dir.glob("*.woff2") if "italic" not in p.name and p.stat().st_size > 400_000]
    numfiles = len(files)
    indx = secrets.randbelow(numfiles)
    src = files[indx]
    print(f"{indx}/{numfiles} -> {src.name} selected")
    ttf_path = src.with_suffix(".ttf")
    if ttf_path.exists():
        ttf_path.rename(dst)


if __name__ == "__main__":
    raise SystemExit(main())
