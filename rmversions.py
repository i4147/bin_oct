#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that takes a requirements.txt file path as a command-line argument and cleans it up.
The script should read the file, skip blank lines and comments, and strip version specifiers (such as >, <, =, ~) from each package entry to extract just the package name.
It should deduplicate the package names, write them back to the same file sorted alphabetically one per line, and print a message showing the file name and the count of unique packages written."""

from __future__ import annotations
import sys
from pathlib import Path


def clean_requirements(fname: str) -> None:
    with Path(fname).open(encoding="utf-8") as f:
        lines = f.readlines()
    packages = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = line.split(">")[0].split("<")[0].split("=")[0].split("~")[0].strip()
        if pkg:
            packages.add(pkg)
    Path(fname).write_text("\n".join(sorted(packages)), encoding="utf-8")
    print(f"Updated  {fname} with {len(packages)} unique packages.")


if __name__ == "__main__":
    fn = sys.argv[1]
    clean_requirements(fn)
