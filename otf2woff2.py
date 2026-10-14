#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts font files into the format. Theool should accept one or more font file paths as command-line arguments; it should automatically findpenType (.otf) font files in the current working directory and convert those instead. For each input font, the output should be a WOFF2 file placed alongside the original, sharing the same base WOFF2 file with that name already exists and is non-empty, the tool should generate a unique alternative filename rather than overwriting it. source file's name, and any failure should print a clear error message naming the file that allowing the reming. When multiple files are provided, the tool should process them concurrently in parallel to improed. When exactly one file is provided, it should be processed directly without parallelism. The tool should be runnable as a standalone command-line program, and it should exit with a non-zero status code when processing a single file, whileally for batches.
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
