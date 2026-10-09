#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that takes a file path as its argument, reads the text file's contents, and filters its lines to keep only non-empty lines containing either "mkv" or "mp4" along with a resolution marker, preferring "480" if present in the file, otherwise falling back to 720.
If any matching lines are found, overwrite the original file with just those filtered lines (joined by newlines); if none are found, leave the file unchanged.
Finally, print the count of matching lines found in the format "{count} links found."""

from __future__ import annotations
from pathlib import Path
import sys


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    content = fn.read_text(encoding="utf-8")
    lines = content.splitlines()
    lowest = "480" if "480" in content else "720"
    nl = [line for line in lines if line.strip() and ("mkv" in line or "mp4" in line) and (lowest in line)]
    if nl:
        fn.write_text("\n".join(nl), encoding="utf-8")
    print(f"{len(nl)} links found.")
