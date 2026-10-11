#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script which organizes files in a directory tree into folders named by file extension. The prompt should be in English, with no code and no preamble.

---

Create a Python 3 script (intended to run under Termux on Android, using the shebang path for Termux's Python) that organizes every file beneath a given root directory into subfolders named after each file's extension.

**Purpose:** Recursively scan a working directory and move each regular file into a top-level folder whose name is the file's extension in lowercase (without the leading dot). Files with no extension go into a folder named "no_extension".

**Inputs and outputs:**
- Input: a root directory path (the current working directory or one passed in). Convert it to a Path object.
- Output: files are physically moved within that root. The function should return nothing, but it should build and maintain an internal statistics mapping per extension containing a file count, a cumulative total byte size, and the list of file paths. Printing or logging of these statistics is optional; if included, keep it concise.

**Dependencies:** Use only the standard library (`contextlib`, `shutil`, `pathlib`, and `from __future__ import annotations`). The script also imports a helper named `gsz` from a local module called `dh`, which is presumed to be a human-readable size formatter that takes a byte count and returns a string. Reproduce that import as-is; if it is intended for reporting sizes, use it when displaying totals.

**Key logic:**
1. Walk the entire tree recursively using a glob for all entries.
2. Skip any entry whose file name is exactly ".gitignore".
3. Skip any entry that has ".git" among its path parts, so the git directory is never touched.
4. Only process regular files (not directories or symlinks to directories).
5. Determine the extension: the suffix lowercased with the leading dot removed, or "no_extension" if there is no suffix.
6. Record the file's size via its stat result and accumulate per-extension statistics, creating the entry on first sight.
7. Only after the full scan, iterate over the collected extensions. For each, create the target directory named after the extension inside the root, using `exist_ok=True` so existing folders are reused. Track created directory names in a set.
8. For each collected file, skip it if its parent already equals the target directory (already organized).
9. Compute the destination path as the target directory plus the original file name. If that name already exists, append a numeric suffix in the form `<stem>_<counter><suffix>`, starting the counter at 1 and incrementing until a free name is found.
10. Move the file with `shutil.move`, converting Path objects to strings. Wrap the move in `contextlib.suppress(BaseException)` so that any failure on an individual file is silently ignored and processing continues with the next file.

**Notable behavior and edge cases:**
- Collecting all files before moving prevents the walk from encountering files moved into new folders mid-iteration.
- Files that are already inside the correct extension folder are left alone.
- Files already inside a folder that has the same name as their extension but nested deeper are still moved to the top-level extension folder.
- Name collisions are resolved non-destructively via numeric suffixes; no file is overwritten.
- Errors during moves are suppressed deliberately, so the script should not crash on permission problems, locked files, or vanished paths. Do not add extra error reporting unless it is harmless.
- Hidden files other than `.gitignore` and the `.git` directory are processed normally.
- Extension directories created at the root may themselves be picked up by a later run; the parent-equality check handles repeat runs idempotently.
- Lowercasing the extension means `.JPG` and `.jpg` share a folder.

**Execution and usage:**
- The script should define the folderize function and, under a standard `__main__` guard, call it with the current working directory (`Path.cwd()` or equivalent). Include the Termux shebang line at the top.
- It should be runnable directly as `python <scriptname>.py` from the target directory, with no required arguments.
- Make the code idiomatic, with type hints where helpful and no third-party dependencies beyond the local `dh` helper.
---"""

from __future__ import annotations

import contextlib
import shutil
from pathlib import Path

from dh import gsz


def folderize_by_extension(cwd: Path):
    root_path = Path(cwd)
    extension_stats = {}
    for path in root_path.rglob("*"):
        if path.name == ".gitignore":
            continue
        if ".git" in path.parts:
            continue
        if path.is_file():
            ext = path.suffix.lower()[1:] if path.suffix else "no_extension"
            size = path.stat().st_size
            if ext not in extension_stats:
                extension_stats[ext] = {"count": 0, "total_size": 0, "files": []}
            extension_stats[ext]["count"] += 1
            extension_stats[ext]["total_size"] += size
            extension_stats[ext]["files"].append(path)
    created_dirs = set()
    for ext, stats in extension_stats.items():
        target_dir = root_path / ext
        target_dir.mkdir(exist_ok=True)
        created_dirs.add(ext)
        for path in stats["files"]:
            if path.parent == target_dir:
                continue
            target_path = target_dir / path.name
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{path.stem}_{counter}{path.suffix}"
                counter += 1
            with contextlib.suppress(BaseException):
                shutil.move(str(path), str(target_path))
    for dir_path in sorted(root_path.glob("**/*"), key=lambda p: len(p.parts), reverse=True):
        if dir_path.is_dir() and dir_path != root_path:
            with contextlib.suppress(OSError):
                dir_path.rmdir()
    total_files = 0
    total_size = 0
    for ext in sorted(extension_stats.keys()):
        stats = extension_stats[ext]
        total_files += stats["count"]
        total_size += stats["total_size"]
        ext_display = ext or "no_extension"
        size_str = gsz(stats["total_size"])
        print(f"{ext_display:<15} : {stats['count']:4} file{'s' if stats['count'] != 1 else ' '}  {size_str:>8}")
    print("-" * 40)
    print(f"{'TOTAL':<15} : {total_files:4} files  {gsz(total_size):>8}")
    print("=" * 40)
    return created_dirs, extension_stats


if __name__ == "__main__":
    target_dir = Path.cwd()
    created_dirs, stats = folderize_by_extension(target_dir)
    print(f"\nCreated {len(created_dirs)} extension folders.")
