#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that renames files to lowercase filenames, using a custom `mpf` (multiprocessing) helper and a `unique_path` utility imported from a local `dh` module.
For each file, it checks existence (falling back to a lowercased path if the original doesn't exist), skips files already lowercase, and if the target lowercase name already exists it resolves the conflict via `unique_path` before renaming, printing the old and new names.
When run without arguments it processes only the top-level files in the current directory; when run with any argument it recursively processes all files in the current directory tree, excluding `.git` paths and symlinks."""

from __future__ import annotations

import sys
from pathlib import Path

from dh import mpf, unique_path


def process_file(path) -> None:
    path = Path(path)
    if not path.exists():
        path = Path(str(path).lower())
        if not path.exists():
            return
    new_name = path.name.lower()
    if new_name == path.name:
        return
    new_path = path.with_name(new_name)
    if new_path.exists():
        new_path = unique_path(new_path)
    path.rename(new_path)
    print(f"{path.name} -> {new_path.name}")


if __name__ == "__main__":
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = (
        list(cwd.glob("*")) if not args else [p for p in cwd.rglob("*") if ".git" not in p.parts and not p.is_symlink()]
    )
    mpf(process_file, files)
