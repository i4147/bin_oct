#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that removes a specific "Requires-Dist" dependency line from all installed package METADATA files under Termux's Python site-packages directory.
The script should determine the current Python version to build the site-packages path, accept the dependency name to remove as a command-line argument, then recursively search for all METADATA files within that directory.
For each METADATA file, it should check whether a line matching "Requires-Dist: <given text>" exists, and if so, remove that line, rewrite the file with the remaining content, and print a message indicating which package (parent directory name) was updated."""

from __future__ import annotations
import sys
from pathlib import Path


def process_file(path: Path, text: str) -> None:
    path = Path(path)
    content = path.read_text()
    target = "Requires-Dist: " + text
    if target in content:
        lines = content.splitlines()
        nl = [line for line in lines if target not in line]
        newcontent = "\n".join(nl)
        path.write_text(newcontent, encoding="utf-8")
        print(f"{path.parent.name} updated.")


if __name__ == "__main__":
    major, minor, _, _, _ = sys.version_info
    py_version = f"{major}{minor}"
    cwd = Path(f"/data/data/com.termux/files/usr/lib/python{py_version}/site-packages")
    target = sys.argv[1]
    for path in cwd.rglob("METADATA"):
        process_file(path, target)
