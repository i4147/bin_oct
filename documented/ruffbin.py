#!/data/data/com.termux/files/usr/bin/env python
"""ruffbin.py -- format the Python scripts with ``ruff format``."""

from __future__ import annotations

from pathlib import Path

from dh import runcmd


def process_file(path: Path):
    """Format one file with ``ruff format`` and report what ruff prints."""
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
