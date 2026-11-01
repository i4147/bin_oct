#!/data/data/com.termux/files/usr/bin/env python
"""decode_unicode.py -- reduce a file to plain ASCII.

Text is NFKD-normalised and the remaining non-ASCII characters are dropped, which turns
accented look-alikes into their ASCII form.
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

if __name__ == "__main__":
    path = Path(sys.argv[1].strip())
    text = path.read_text(encoding="utf-8")
    result = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    path.write_text(result, encoding="utf-8")
    print(f"{path} updated")
