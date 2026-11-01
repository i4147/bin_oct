#!/data/data/com.termux/files/usr/bin/env python
"""find_req.py -- search package metadata for a requirement.

``METADATA`` files are scanned for a ``Requires-Dist`` entry that matches the given
text.
"""

from __future__ import annotations

import sys
from pathlib import Path


def process_file(path: Path, text: str) -> None:
    """Search *text* for the ``Requires-Dist`` entry of *path* and report a match."""
    path = Path(path)
    content = path.read_text().lower()
    target1 = "requires-dist: " + text
    if target1 in content:
        print(path.parent.name)


if __name__ == "__main__":
    cwd = Path("/data/data/com.termux/files/home/.local/lib/python3.14/site-packages")
    target = sys.argv[1]
    for path in cwd.rglob("METADATA"):
        process_file(path, target)
