#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that searches through a local Python site-packages directory for installed package metadata files and reports which installed packages declare a given dependency. The script should accept a dependency name as a command-line argument, recursively scan all package metadata files under a configurable base directory (defaulting to a typical Python 3.14 site-packages location on Termux), and check each metadata file for a declared dependency requirement matching the provided name, performing the comparison case-insensitively. For every package whose metadata declares that dependency, the script should print the name of the package's directory. The script should handle files that cannot be read gracefully without stopping the overall scan, and should exit with a clear usage message if no dependency name is supplied. Keep the output minimal: one matching package name per line, with no additional commentary.
---"""

from __future__ import annotations
from pathlib import Path
import sys


def process_file(path: Path, text: str) -> None:
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
