#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively scans the current working directory for subdirectories containing a ".git" folder, identifying them as git repositories.
For each such repository found, it should delete all other files and subdirectories inside it (keeping only the ".git" folder itself), using shutil.rmtree for directories and unlink for files.
After processing, the script should print the relative paths of all top-level items remaining in the current working directory."""

from __future__ import annotations

import shutil
from pathlib import Path


def process_dir(pardir: Path) -> bool:
    dotgit = pardir / ".git"
    if not dotgit.exists():
        return False
    for path in pardir.glob("*"):
        if path.is_dir() and path.name != ".git":
            shutil.rmtree(str(path))
        if path.is_file():
            path.unlink()
    return True


def find_targets(cwd: Path) -> None:
    for dpath in cwd.rglob("*"):
        if dpath.is_dir() and dpath.name == ".git":
            parent_of_dotgit = dpath.parent
            process_dir(parent_of_dotgit)


if __name__ == "__main__":
    cwd = Path.cwd()
    find_targets(cwd)
    for p in cwd.glob("*"):
        print(p.relative_to(cwd))
