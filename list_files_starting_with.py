#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
from pathlib import Path
import sys


def main() -> None:
    prefix = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if not prefix:
        print("Usage: python script.py <prefix>", file=sys.stderr)
        sys.exit(1)
    for entry in Path.cwd().iterdir():
        if entry.name.startswith(prefix) and not entry.is_symlink():
            print(entry.name)


if __name__ == "__main__":
    raise SystemExit(main())
