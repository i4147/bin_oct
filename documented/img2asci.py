#!/data/data/com.termux/files/usr/bin/env python
"""img2asci.py -- render images as ASCII art in the terminal.

Each image is converted with ``AsciiArt`` and sized to the current terminal width.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ascii_magic import AsciiArt
from dh import get_files


def process_file(image_path: Path) -> None:
    image_path = Path(image_path)
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
