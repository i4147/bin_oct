#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that runs in a Termux-style Android environment and randomly selects a terminal font from a directory of font files. The script should scan a fixed font folder on shared storage for WOFF2 web font files, ignoring any whose names indicate an italic style and any that are too small to be a full font (under roughly 400 KB). From the remaining candidates, it should pick one at random using a cryptographically secure random source, and report to the user which file was chosen along with its position among the candidates and the total count.
The script should then install the chosen font as the active terminal font by placing it at the expected Termux font location in the user's home directory, replacing any previously installed font there. Conversion from WOFF2 to TTF should be attempted with an available font-processing library, and failures during conversion should be handled gracefully without crashing. If no suitable candidate fonts are found, the script should handle that case cleanly rather than failing with an unexpected error. Keep the behavior simple, self-contained, and suitable for running from the command line, exiting with a standard status code when finished.
---"""

from __future__ import annotations
from pathlib import Path
import secrets


def convert_with_fonttools(src, dst):
    from fontTools.ttLib import woff2

    try:
        woff2.decompress(src, dst)
    except Exception as e:
        return


def main():
    source_dir = Path("/sdcard/font")
    dst = Path.home() / ".termux" / "font.ttf"
    if dst.exists():
        dst.unlink()
    files = [p for p in source_dir.glob("*.woff2") if "italic" not in p.name and p.stat().st_size > 400_000]
    numfiles = len(files)
    indx = secrets.randbelow(numfiles)
    src = files[indx]
    print(f"{indx}/{numfiles} -> {src.name} selected")
    ttf_path = src.with_suffix(".ttf")
    if ttf_path.exists():
        ttf_path.rename(dst)


if __name__ == "__main__":
    raise SystemExit(main())
