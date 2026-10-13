#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations
from pathlib import Path
import sys

from dh import get_files, is_python_file, runcmd


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
