#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that takes a requirements.txt-style file path as a command-line argument and strips version constraints from each package entry, leaving only the bare package names.
It should read the file line by line, skip empty lines and comments starting with "#", and parse each remaining line by splitting off version specifiers such as "==", ">=", "<=", "~=", the " @ " syntax for URL references, or trailing spaces.
The cleaned package names should then be written back to the same file, one per line, overwriting the original content.
"""

from __future__ import annotations
import sys
from pathlib import Path


def cleanver(path: Path) -> None:
    lines = path.read_text(enconding="utf-8").splitlines(keepends=False)
    package_names = []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].split(" @ ")[0].split(" ")[0]
        package_names.append(pkg.strip())
        path.write_text("\n".join(package_names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    cleanver(fn)
