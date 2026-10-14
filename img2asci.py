#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that renders images as colored ASCII art directly in the terminal. The tool should accept one or more image file paths as command-line arguments; if no arguments are given, it should automatically discover supported image files (JPG, PNG, BMP, WEBP) in the current working directory and render those instead. Each image should be converted to ASCII art sized to fit the current terminal width, with the aspect ratio compensated so the output does not look stretched (characters are typically taller than they are wide). The output should be in full color, not monochrome.
When a single image is provided, process it directly and exit cleanly with a success status. When multiple images are provided, process them concurrently using a pool of worker processes (around eight), so that the rendering of several images overlaps in time, and wait for all of them to finish before exiting. The script should be robust to a missing or invalid file path by reporting a clear error for that file rather than crashing the entire run, and it should exit with an appropriate status code when the program completes. Keep the overall design simple and readable, with a clear entry point guarded so the script can also be imported without side effects.
---"""

from __future__ import annotations
import os
from pathlib import Path
import sys
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
