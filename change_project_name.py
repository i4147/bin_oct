#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that recursively performs find-and-replace across an entire directory tree, taking two arguments (old text and new text).
It should walk all files under the current directory, read each as UTF-8 text (ignoring decode/permission errors) and replace every occurrence of the old string with the new one, writing changes back in place.
After updating file contents, it should also rename any files or folders whose names contain the old text, processing deepest paths first to avoid path conflicts, and skip renaming (with a warning message) if a target name already exists.
The script should print a usage message and exit with an error if not given exactly two command-line arguments."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path


def replace_in_file(path: Path, old: str, new: str) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except (UnicodeDecodeError, PermissionError):
        return
    if old not in text:
        return
    new_text = text.replace(old, new)
    path.write_text(new_text, encoding="utf-8")


def rename_path(path: Path, old: str, new: str) -> Path:
    if old not in path.name:
        return path
    new_name = path.name.replace(old, new)
    new_path = path.parent / new_name
    if new_path.exists():
        print(f"path by name {new_path} already exists\n rename it manually")
        return path
    try:
        shutil.move(str(path), str(new_path))
        return new_path
    except Exception:
        return path


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <text_to_change> <replacement_text>")
        sys.exit(1)
    old = sys.argv[1]
    new = sys.argv[2]
    root = Path()
    for path in list(root.rglob("*")):
        if path.is_file():
            replace_in_file(path, old, new)
    paths = sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    for path in paths:
        rename_path(path, old, new)


if __name__ == "__main__":
    raise SystemExit(main())
