#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that batch-converts TTF/OTF font files into the WOFF format using fontTools.
It should accept file paths as command-line arguments, or if none are given, automatically collect all .ttf and .otf files in the current working directory.
For each font, it loads it with TTFont, sets its flavor to "woff", saves it under the same name with a .woff extension (generating a unique filename if one already exists), deletes the original source file on success, and prints a confirmation or error message.
If only a single file is processed it should run synchronously, otherwise it should process the files in parallel using a multiprocessing helper."""

from __future__ import annotations
import sys
from pathlib import Path
from dh import cprint, get_files, mpf, unique_path
from fontTools.ttLib import TTFont

cwd = Path.cwd()


def process_file(path: Path) -> None:
    path = Path(path)
    woff_path = path.with_suffix(".woff")
    if woff_path.exists() and woff_path.stat().st_size:
        woff_path = unique_path(woff_path)
    try:
        font = TTFont(path)
        font.flavor = "woff"
        font.save(woff_path)
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
