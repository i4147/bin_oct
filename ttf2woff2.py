#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that batch-converts TTF/OTF font files into WOFF2 format using fontTools' woff2 module.
It should accept file paths as command-line arguments, or if none are given, automatically discover all .ttf and .otf files in the current working directory via a helper function.
For each font file, it compresses it to a .woff2 file (generating a unique filename if one already exists and is non-empty), deletes the original file on success, and prints a confirmation message, while printing a colored error message on failure without crashing.
If multiple files are processed, it should use a multiprocessing helper to handle them in parallel; if only a single file is given, it should process it directly and exit with status code 1."""

from __future__ import annotations
import sys
from pathlib import Path
from dh import cprint, get_files, mpf, unique_path
from fontTools.ttLib import woff2

cwd = Path.cwd()


def process_file(path: Path) -> None:
    path = Path(path)
    woff2_path = path.with_suffix(".woff2")
    if woff2_path.exists() and woff2_path.stat().st_size:
        woff2_path = unique_path(woff2_path)
    try:
        woff2.compress(path, woff2_path)
        print(f"{path.name} converted.")
        path.unlink()
    except:
        cprint(f"error convering {path.name}")


def main() -> None:
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".ttf", ".otf"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
