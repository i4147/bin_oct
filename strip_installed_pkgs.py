#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans up a requirements file by removing entries that do not need to be installed. The script should accept an optional path to a requirements file as a command-line argument, defaulting to a standard "requirements.txt" in the current directory if none is given.
The script should read the requirements file, ignoring blank lines and comment lines. It should normalize each package name so that differences in case and in hyphen versus underscore spelling are treated as equivalent. It should then remove any package that is already installed in the current Python environment, and any package that belongs to the Python standard library, since these never need to be listed as dependencies.
After filtering, the script should remove duplicate entries, sort the remaining names alphabetically, and overwrite the original file with the cleaned list using UTF-8 encoding, one package per line with a trailing newline. Finally, it should print a short message to the console stating how many packages were removed.
The script should handle the case where the file is missing or unreadable by reporting a clear error rather than crashing with an unhandled traceback, and it should not modify the file if no changes are needed. Choose any suitable libraries and internal structure, provided the observable behavior described above is preserved.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import STDLIB, get_installed_pkgs


def read_requirements(filename) -> list[str]:
    req_file = Path(filename)
    with req_file.open(encoding="utf-8") as f:
        return [line.strip().replace("-", "_").lower() for line in f if line.strip() and not line.startswith("#")]


def strip_installed_from_requirements(fname: str) -> None:
    installed = get_installed_pkgs()
    installed = [p.lower().replace("-", "_") for p in installed if p]
    lines = read_requirements(fname)
    new_lines = [line for line in lines if line not in installed]
    new_lines = [line for line in new_lines if line not in STDLIB]
    new_lines = sorted(set(new_lines))
    Path(fname).write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    removed = len(lines) - len(new_lines)
    print(f"Removed {removed} packages")


if __name__ == "__main__":
    fn = "requirements.txt"
    if len(sys.argv) > 1:
        fn = sys.argv[1]
    strip_installed_from_requirements(fn)
