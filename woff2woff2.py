#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that batch-converts WOFF font files to WOFF2 format using accept file paths as command-line arguments, or if none are given, automatically discover all ".woff" files in the current working directory via a helper function.
For each file, it loads the font with TTFont, sets its flavor to "woff2", saves it with a ".woff2" extension (generating a unique filename if a non-empty target already exists), deletes the original ".woff" file, and prints a success or error message per file.
If exactly one file is processed it runs synchronously and exits with status 1, otherwise it processes all files in parallel using a multiprocessing helper function."""

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
