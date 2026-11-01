#!/data/data/com.termux/files/usr/bin/env python
"""decode_phonetic.py -- expand phonetic escapes in a file.

The file is decoded and written back in place.
"""

from __future__ import annotations

import sys
from html import unescape
from pathlib import Path


def main() -> None:
    """Rewrite the file named on the command line with its phonetic escapes expanded."""
    fn = Path(sys.argv[1])
    content = fn.read_text(encoding="utf-8", errors="replace")
    fn.write_text(unescape(content), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
