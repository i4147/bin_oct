#!/data/data/com.termux/files/usr/bin/python
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
