#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations
from pathlib import Path
import shutil


def main() -> None:
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
