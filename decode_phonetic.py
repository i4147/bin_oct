#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path as a command-line argument, reads the file's text content (tolerating invalid or mixed-encoding bytes without crashing), decodes all HTML character entities in that text (such as named entities like "&amp;" or "&lt;" and numeric entities), and overwrites the same file with the decoded result, saving it as UTF-8. The script should run as a standalone command-line tool, exit cleanly on success, and be designed to handle typical text or HTML files in a simple, one-shot, in-place transformation.
---"""

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
