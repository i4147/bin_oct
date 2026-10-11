#!/data/data/com.termux/files/usr/bin/env python
"""You are writing a single Python 3 script (standard library only, no third-party packages) that recursively performs a text find-and-replace across the current working directory, then renames any file or directory whose name contains the same search text. Write the script so it can be run directly and reproduces the behavior described below.

**Purpose and usage**
- The script takes exactly two command-line arguments: the text to find (`old`) and the replacement text (`new`).
- If the argument count is not exactly two, print a usage line that includes the script's own name (`sys.argv[0]`) and the placeholders `<text_to_change>` and `<replacement_text>`, then exit with status 1.
- Start the file with a Termux-specific shebang line for Python (`/data/data/com.termux/files/usr/bin/env python`), and include `from __future__ import annotations` at the top.
- The script should be runnable as `__main__`; the entry point should call `main()` and raise `SystemExit` with its return value.

**Phase 1: content replacement**
- Use `pathlib.Path()` (the current directory) and recursively enumerate everything with `rglob("*")`. Snapshot this into a list before iterating so later changes do not affect the loop.
- For each entry that is a regular file, call a helper `replace_in_file(path, old, new)`.
- `replace_in_file` reads the file as UTF-8 with `errors="ignore"`. If reading raises `UnicodeDecodeError` or `PermissionError`, silently skip the file. If the search text is not present, return without writing. Otherwise replace all occurrences and write the result back with UTF-8 encoding. Do not create backups.

**Phase 2: renaming**
- Re-enumerate all entries with `rglob("*")` after content replacement, and sort them by depth (number of path parts) in descending order, so the deepest paths are renamed first and parent directories are renamed after their children.
- For each path, call `rename_path(path, old, new)`, which returns a `Path`.
- `rename_path` does nothing if the search text is not in the entry's name (name only, not the full path). Otherwise it builds the new name by replacing all occurrences in the name, and forms the new path in the same parent directory.
- If a target with the new name already exists, print a message in the form `path by name <new_path> already exists` followed by a newline and ` rename it manually`, then leave the original unchanged and return the original path.
- Otherwise attempt `shutil.move` from the original to the new path (converted to string). On success return the new path. On any `Exception`, silently return the original path.
- Note that because paths in the second listing may have been renamed earlier in the same loop, the code tolerates stale references by simply returning the original path on failure rather than raising.

**Edge cases and behavior to preserve**
- Only the file contents are changed in phase 1; directories are never read or written, and phase 2 handles both files and directories by name.
- Matching is plain substring replacement (no regex, no case folding). An empty search string is not specially guarded; `str.replace` with an empty pattern will be applied as-is.
- The script never prompts for confirmation and never deletes anything.
- Files that cannot be decoded as UTF-8 are left untouched in content but may still be renamed in phase 2.
- Errors during rename are swallowed; only the name-collision case prints a message.

**Output requirements**
- Use type hints (`Path`, `str`, `-> None`, `-> Path`) and keep the code short and idiomatic, with no docstrings or comments beyond what is necessary.
- Print nothing on success apart from collision warnings and the usage message.
- Deliver only the complete script in one code block.
---"""

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
