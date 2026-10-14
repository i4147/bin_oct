#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively walks the current working directory and automatically formats every eligible file using the Ruff code formatter. The script should visit all subdirectories, skip symbolic links and anything located inside a version-control metadata folder (such as `.git`), and only process regular files that have no file extension. Each selected file should be passed to the Ruff formatter, with its output shown in the console. Formatting failures for individual files should be handled silently so the script continues processing the remaining files without stopping. The script should run as a standalone command-line tool with no required arguments, operating on the directory from which it is launched.
---"""

from __future__ import annotations
from pathlib import Path
from dh import runcmd


def process_file(path: Path):
    try:
        runcmd(["ruff", "format", str(path)], show_output=True)
    except:
        return


if __name__ == "__main__":
    cwd = Path.cwd()
    for r, d, files in cwd.walk():
        for file in files:
            path = r / file
            if path.is_symlink():
                continue
            if ".git" in path.parts:
                continue
            if path.is_file() and not path.suffix:
                process_file(path)
