#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts font files to the WOFF2 web font format. The tool should accept one or more font file paths as command-line arguments; if no arguments are given, it should automatically find all TrueType (.ttf) and OpenType (.otf) font files in the current working directory and convert those. For each input font, it should produce a WOFF2 file placed alongside the original, using the same base name with a .woff2 extension. If a WOFF2 file with that name already exists and is non-empty, the tool should generate a unique alternative filename rather than overwriting it. After a successful conversion, the original font file should be deleted, and a short confirmation message naming the converted file should be printed. If a conversion fails, the tool should report an error for that specific file without stopping the processing of other files, and the original file should be left untouched. When multiple files are supplied, they should be processed concurrently in parallel to speed up the batch. When exactly one file is supplied, it should be processed directly, and the script should exit with a non-zero status code after handling it. The tool should be a simple, dependency-light command-line utility suitable for batch font conversion in a developer's workflow.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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
