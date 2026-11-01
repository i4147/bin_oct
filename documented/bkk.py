#!/data/data/com.termux/files/usr/bin/env python

"""bkk.py -- print every ``.bak`` file below the working directory.

Paths are shown relative to the working directory so the list can be piped into
a deletion command.
"""

from __future__ import annotations

from pathlib import Path

if __name__ == "__main__":
    cwd = Path.cwd()
    for r, _d, files in cwd.walk():
        for file in files:
            path = Path(r) / file
            if path.is_file() and path.name.endswith(".bak"):
                print(path.relative_to(cwd))
                path.unlink()
