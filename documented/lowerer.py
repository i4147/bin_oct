#!/data/data/com.termux/files/usr/bin/env python
"""lowerer.py -- lower-case the contents of a file."""

import sys
from pathlib import Path


def main():
    """Rewrite the file named on the command line in lower case."""
    fn = Path(sys.argv[1])
    content = fn.read_text(encoding="utf-8")
    lower_content = content.lower()
    fn.write_text(lower_content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
