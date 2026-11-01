#!/data/data/com.termux/files/usr/bin/env python
"""fv.py -- page through a text file.

The file is shown with the pager ``pydoc`` installs, so the output is read-only and
scrollable.
"""

from __future__ import annotations

import pydoc
import sys
from pathlib import Path


def main() -> None:
    """Show the file named on the command line in a pager.

    The text is decoded with replacement characters so binary files still display
    something.
    """
    pydoc.pager(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))


if __name__ == "__main__":
    raise SystemExit(main())
