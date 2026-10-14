#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts font files to the WOFF2 web font format. The tool should accept one or more font file paths as command-line arguments; if no arguments are given, it should scan the current working directory for WOFF font files and process those instead. For each input file, produce a WOFF2 version alongside it with the same base name and a .woff2 extension. If a WOFF2 file with that name already exists and is non-empty, do not overwrite it; instead, gener print a confirmation message with the file name and remove the original source file. If conversion fails for a file, report an error message naming that file and leave the original untouched. When multiple files are given, process them in parallel to speed up batch conversion. When exactly one file is given, process it directly and exit with a non-zero status code to signal completion. Use a clean command-line entry point that returns an exit status on completion.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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
        path.unlink()
    except:
        cprint(f"error convering {path.name}")


def main() -> None:
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".woff"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
