#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory recursively and removes broken symbolic links, reporting each action to the user. The tool should skip anything located inside version-control metadata folders. It must support a dry-run mode, activated by a command-line flag, in which broken links are only listed and not deleted. In normal mode, each broken link found should be deleted and a message printed naming the file removed. In dry-run mode, each broken link should be reported with a note that it would be removed if the flag were omitted. The script should run its main logic from the command line, exit cleanly with a status code when finished, and require no third-party dependencies.
---"""

from __future__ import annotations
from pathlib import Path
import sys


def blink(directory: Path) -> None:
    for root, _, files in directory.walk():
        for f in files:
            fullpath = Path(root) / f
            if ".git" in fullpath.parts:
                continue
            if fullpath.is_symlink() and not fullpath.exists():
                if "-d" not in sys.argv:
                    fullpath.unlink()
                    print(f" - {f} removed.")
                else:
                    print(f" - {f} (rerun without -d to remove")


def main():
    cwd = Path.cwd()
    blink(cwd)


if __name__ == "__main__":
    raise SystemExit(main())
