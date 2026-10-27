#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
from html import unescape
from pathlib import Path
import sys


def main() -> None:
    fn = Path(sys.argv[1])
    content = fn.read_text(encoding="utf-8", errors="replace")
    fn.write_text(unescape(content), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
