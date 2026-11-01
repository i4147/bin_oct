#!/data/data/com.termux/files/usr/bin/env python

"""480mkv.py -- keep only the download links for the lowest offered resolution.

Reads a text file of video links, decides whether 480p links exist (falling
back to 720p when they do not), and rewrites the file with just those
``mkv``/``mp4`` lines.  The rewrite only happens when at least one matching
line was found; the number of matches is printed either way.

Usage: ``480mkv.py LINKS.txt``
"""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    fn = Path(sys.argv[1])
    content = fn.read_text(encoding="utf-8")
    lines = content.splitlines()
    # Keep the lowest resolution the page offers: 480p when present, else 720p.
    lowest = "480" if "480" in content else "720"
    nl = [line for line in lines if line.strip() and ("mkv" in line or "mp4" in line) and (lowest in line)]
    if nl:
        fn.write_text("\n".join(nl), encoding="utf-8")
    print(f"{len(nl)} links found.")
