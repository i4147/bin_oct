#!/data/data/com.termux/files/usr/bin/env python
"""foext.py -- group the files of a directory by extension.

Every file in the working directory is moved into a sub-folder named after its extension
(or ``no_extension``).
"""

from __future__ import annotations

import shutil
from pathlib import Path


def main() -> None:
    """Move every file of the working directory into a folder named after its extension.

    Files without an extension go into ``no_extension``.
    """
    cwd = Path.cwd()
    for item in cwd.iterdir():
        if not item.is_file():
            continue
        ext = item.suffix.lower().lstrip(".") or "no_extension"
        target_dir = cwd / ext
        target_dir.mkdir(exist_ok=True)
        shutil.move(str(item), target_dir / item.name)


if __name__ == "__main__":
    raise SystemExit(main())
