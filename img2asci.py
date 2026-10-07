#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that converts one or more image files into colored ASCII art and prints them directly to the terminal.
It should accept image file paths as command-line arguments, or if none are given, automatically discover image files (jpg, png, bmp, webp) in the current working directory using a helper `get_files` function.
Use the `ascii_magic` library's `AsciiArt.from_image` to render each image, sizing the output to the current terminal width with a width ratio of 2 and preserving color (non-monochrome).
If only a single file is provided or found, process it directly and exit; otherwise, process multiple files concurrently using a multiprocessing pool of 8 workers."""

from __future__ import annotations
import os
import sys
from pathlib import Path
from ascii_magic import AsciiArt
from dh import get_files


def process_file(image_path: Path) -> None:
    Path(path)
    art = AsciiArt.from_image(image_path)
    art.to_terminal(columns=os.get_terminal_size().columns, width_ratio=2, monochrome=False)


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(arg) for arg in args] if args else get_files(cwd, ext=[".jpg", ".png", ".bmp", ".webp"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    pool = Pool(8)
    for _ in pool.imap_unordered(process_file, files):
        pass
    pool.close()
    pool.join()


if __name__ == "__main__":
    raise SystemExit(main())
