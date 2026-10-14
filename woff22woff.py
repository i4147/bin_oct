#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts font files into the WOFF web font format. The tool should accept one or more font file paths as command-line arguments; if no arguments are given, it should automatically find all TrueType (.ttf) and OpenType (.otf) font files in the current working directory and convert those instead. For each input font, produce a WOFF version saved alongside the original with the same base name and a .woff extension. If a file with that name already exists and is non-empty, generate a unique alternative filename rather than overwriting it. After a successful conversion, print a short confirmation message with the file name and delete the original source font file. If a conversion fails for any file, report an error message naming that file and continue processing the remaining files without stopping. When a single file is provided, process it directly; when multiple files are provided, process them in parallel to speed up batch conversion. The script should exit with a non-zero status code when run on a single file and handle the overall run cleanly, with all user-facing output kept concise and informative.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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
