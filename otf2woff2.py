#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that batch-converts OTF font files into WOFF2 format using fontTools.
It should accept file paths as command-line arguments, or if none are given, automatically gather all ".otf" files from the current working directory via a helper function.
For each font, it loads it with TTFont, sets the flavor to "woff2", and saves it to a same-named ".woff2" file, generating a unique filename if a non-empty target already exists, while printing success messages or a colored error message on failure.
If only a single file is processed it should run synchronously and exit, otherwise it should process the files in parallel using a multiprocessing helper function.
"""

from __future__ import annotations
import sys
from pathlib import Path
from dh import cprint, get_files, mpf, unique_path
from fontTools.ttLib import TTFont

cwd = Path.cwd()


def process_file(path: Path) -> None:
    path = Path(path)
    woff2_path = path.with_suffix(".woff2")
    if woff2_path.exists() and woff2_path.stat().st_size:
        woff2_path = unique_path(woff2_path)
    try:
        font = TTFont(path)
        font.flavor = "woff2"
        font.save(woff2_path)
        print(f"{path.name} converted.")
    except:
        cprint(f"error convering {path.name}")


def main() -> None:
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".otf"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
