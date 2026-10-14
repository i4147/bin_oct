#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single text file path as its command-line argument, reads the file as UTF-8 text, and filters its lines to keep only non-blank lines that reference video links in MKV or MP4 format at a particular resolution. The script should prefer the 480p resolution: if the text contains "480" anywhere, keep only lines matching 480; otherwise fall back to 720. Save the retained lines back to the same file, one per line, overwriting the original content in UTF-8. When finished, print a short summary message stating how many matching links were found.
---"""

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
