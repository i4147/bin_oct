#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line tool for bulk find-and-replace across a project directory. It should accept exactly two arguments: the text to search for and the replacement text. Starting from the current working directory, it should recursively walk through the project tree and perform two kinds of changes:
1. **Content replacement:** For every readable text file, replace all occurrences of the search text with the replacement text, saving the file in UTF-8. Files that cannot be decoded or cannot be written due to permission issues should be skipped silently without stopping the run.
2. **File and folder renaming:** For every file and directory whose name contains the search text, rename it so the search text is substituted with the replacement text. Renaming should be performed after content updates are considered, and items should be processed so that nested paths remain valid. If the target name already exists, the tool should print a clear warning telling the user to resolve the conflict manually and leave that item unchanged. Any other rename failure should also be handled gracefully without crashing.
Behavior requirements:
- If the number of command-line arguments is not exactly two, print a short usage message showing the expected format and exit with a non-zero status code.
- Skip the script's own file so it is never modified or renamed.
- Only modify files that actually contain the search text; leave all other files untouched.
- Process the entire tree so that changes are applied consistently, including items inside newly renamed directories.
- Provide clear console output summarizing which files were edited and which items were renamed, and report any conflicts or errors encountered.
- Keep the implementation robust, readable, and safe to run on typical project folders, avoiding crashes from unexpected file types or encoding issues.
---"""

from __future__ import annotations
from pathlib import Path
import shutil
import sys


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
