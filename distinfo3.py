#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that asks an AI coding agent to build a Termux-targeted Python script which scans the site-packages directory of the running Python version, identifies `*dist-info` directories, and removes any that contain `top_level.txt` or `entry_points.txt`, printing progress and using a colored output helper. Describe inputs, outputs, dependencies, logic, error handling, edge cases, and execution details without including code.

Create a Python 3 script for Termux (Android) that cleans up stale package metadata from the site-packages directory of the currently running Python interpreter.

Requirements:

**Purpose:** Scan the Termux site-packages directory for metadata directories and remove selected files-bearing dist-info folders, specifically those containing `top_level.txt` or `entry_points.txt`.

**Shebang and encoding:** Use the Termux-specific env shebang pointing to the Python interpreter at `/data/data/com.termux/files/usr/bin/env python`. Begin the file with `from __future__ import annotations`.

**Dependencies:** Use only the standard library modules `shutil`, `sys`, and `pathlib.Path`, plus a third-party-style helper `cprint` imported from a module named `dh` that prints colored text (signature: message string, then a color name such as `"cyan"`). Do not implement `cprint` yourself.

**Version detection:** At import time, unpack the first five fields of `sys.version_info` into major, minor, and three discarded values. Build a `py_version` string in the form `major.minor` (e.g., `3.11`).

**Function `process_dir(dr: Path) -> bool`:**
- Print the directory's name (not full path) to stdout.
- If the directory name contains the substring `dist-info`, iterate over its immediate children. For each child whose name is exactly `top_level.txt` or `entry_points.txt`, print the full directory path followed by " removed" via `cprint` in cyan, then remove the directory recursively with `shutil.rmtree`.
- Note the behavior: the removal call targets the directory itself (`dr`), not the matched file, and it may be invoked once per matching child, so a dist-info folder containing both files may trigger removal twice; the agent should reproduce this faithfully, and handle the second call gracefully if the directory is already gone or should be guarded with a check, but must still preserve the printed messages semantics.
- Always return `True`.

**Function `main() -> None`:**
- Build the target path as `/data/data/com.termux/files/usr/lib/python{py_version}/site-packages` as a `Path`.
- If the path does not exist, return silently with no output or error.
- Iterate over immediate children. For each child that is a directory and contains exactly one entry (checked via `len(list(path.iterdir())) == 1`), call `process_dir` on it. Note that this single-entry condition means the folder is only processed when it has exactly one child; preserve this exact filter.
- Return nothing.

**Entry point:** Under the standard `if __name__ == "__main__":` guard, call `main()` and pass its result to `raise SystemExit(...)`, so the process exits with status code 0 on success.

**Error handling:** The script does not add try/except blocks; permission or filesystem errors from `shutil.rmtree` or `iterdir` will propagate as uncaught exceptions. Preserve this, unless the reproduction notes a deliberate guard for the double-removal case described above.

**Edge cases to handle or preserve:**
- Nonexistent site-packages directory: silent exit.
- Non-directory entries in site-packages: skipped.
- Directories with zero or multiple children: skipped by the single-entry filter.
- Dist-info directories without the target files: name printed, nothing removed.
- Matching files appear only as direct children, not nested.

**Output:** Plain directory names printed to stdout for every top-level directory examined by `process_dir`, plus cyan colored removal notices for each removal action.

**Execution:** Intended to run directly on Termux with a Python interpreter installed under the Termux prefix; the Python version path segment must match the running interpreter. No command-line arguments are accepted.
---"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from dh import cprint

major, minor, _, _, _ = sys.version_info
py_version = f"{major}.{minor}"


def process_dir(dr: Path) -> bool:
    print(dr.name)
    if "dist-info" in dr.name:
        for k in dr.iterdir():
            if k.name in {"top_level.txt", "entry_points.txt"}:
                cprint(f"{dr} removed", "cyan")
                shutil.rmtree(dr)
    return True


def main() -> None:
    cwd = Path(f"/data/data/com.termux/files/usr/lib/python{py_version}/site-packages")
    if not cwd.exists():
        return
    for path in cwd.iterdir():
        if path.is_dir() and len(list(path.iterdir())) == 1:
            process_dir(path)


if __name__ == "__main__":
    raise SystemExit(main())
