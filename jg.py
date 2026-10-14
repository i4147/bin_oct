#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory for Git repositories (folders containing a `.git` subdirectory) and, for each repository root found, deletes all of its contents except the `.git` folder itself. Within each such repository root, every immediate subdirectory other than `.git` should be removed entirely along with its contents, and every regular file directly inside the root should be deleted. Nested repositories discovered during the scan should be handled as well, so that every matching repository root is cleared. Only the top level of each repository should be cleaned; the `.git` metadata must be preserved so the repository remains valid, and the script should report success or skipping for each candidate directory it evaluates.
The script should be runnable directly from the command line with no arguments, operating on the directory it is launched from. After processing is complete, it should print the name of every entry remaining at the top level of the starting directory, shown relative to that directory, so the user can see the result of the operation.
Design the script so that it is safe to run on a directory that contains no Git repositories (it should simply do nothing destructive), handles directories that have a `.git` entry but no other contents gracefully, and does not crash on symbolic links or permission-related issues encountered during deletion. Keep the implementation simple and self-contained, using only the Python standard library.
---"""

from __future__ import annotations
from pathlib import Path
import shutil


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
