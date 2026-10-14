#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that renames files to lowercase names in the current working directory. It should accept an optional command-line argument: when no arguments are given, it processes only the top-level items in the current directory; when any argument is given, it recursively processes everything beneath the current directory, skipping any path that belongs to a version-control metadata folder (such as `.git`) and skipping symbolic links.
For each file it considers, the script should check whether the file exists (and if the given path doesn't resolve, try a lowercase version of the path). If the name is already lowercase, leave it alone. Otherwise, rename the file so that only its filename becomes lowercase while its directory stays the same. If a file with the lowercase name already exists, generate a unique alternative name instead of overwriting anything. After each successful rename, print a concise line showing the old name, an arrow, and the new name.
Process the collected paths concurrently or with a parallel mapping helper, so that the rename work is distributed efficiently across the list. The script should be runnable directly from the command line, must not crash on missing or already-processed entries, and should handle name collisions safely. Use only the standard library plus any helper utilities you judge appropriate, and keep the overall design clean, readable, and robust.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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
