#!/data/data/com.termux/files/usr/bin/env python
"""Write a single self-contained prompt that instructs an AI coding agent to build a Python script with the following specification. Do not include code or snippets.

---

Create a Python 3 command-line script (intended to run under Termux on Android, with a shebang pointing to the Termux Python interpreter) that recursively scans the current working directory and reports every regular file larger than a size threshold, printing each one's path relative to the current directory along with a human-readable size.

**Purpose:** Quickly find large files within the current directory tree, for disk-usage auditing on a mobile or constrained environment.

**Dependencies:**
- Use only the standard library (sys, pathlib, os), plus one external helper: a function named `fsz` imported from a module named `dh` that converts a byte count into a human-readable string (e.g., "1.5 MB"). Do not reimplement it; just import and call it.
- Use `from __future__ import annotations` for type hint compatibility.

**Inputs:**
- Optional single command-line argument: a threshold in megabytes (integer). If provided, it is multiplied by 1024×1024 to get the byte threshold. If absent, the default threshold is 1 MiB (1024 × 1024 bytes).
- No other input; the scan root is always the current working directory, captured once at module load.

**Outputs:**
- One line per qualifying file to standard output, formatted as `<relative path> : <human-readable size>`, where the path is relative to the current working directory and the size is produced by `fsz`.
- Only files whose size is strictly greater than the threshold are printed.
- No output for files at or below the threshold, and no header or summary.

**Core logic:**

1. A generator function takes a root path. If the root is a directory, walk it recursively top-down using `os.walk`:
   - For each directory entry in the current level, build its full path and resolve it. Remove it from the traversal list if it should be skipped (via a `should_skip` predicate) or if its resolved path has already been visited. Record every resolved directory path as visited. Note that the visited-check and skip-check are combined in one condition, and visited paths are recorded for each subdirectory encountered.
   - For each file in the current level, build its path and yield it unless `should_skip` returns true for it.
   - If the root is not a directory (e.g., a single file), yield the root itself without any checks.
   - The `should_skip` predicate is referenced but not defined in this script; it must be provided by the implementer as a helper function (e.g., to skip hidden directories, VCS folders like `.git`, or similar), and it should accept a Path and return a boolean. Document this assumption in the code's behavior: skipping logic is pluggable.

2. A `process_file` function takes a path and a threshold (default: the module-level 1 MiB constant). It gets the file's size from `stat()`. If the size is strictly greater than the threshold, it prints the relative path (relative to the cwd) and the `fsz`-formatted size.

3. `main` parses the threshold from `sys.argv[1]` if present, converting megabytes to bytes; otherwise uses the default. It iterates over all files yielded by the walker from the cwd, skips any path that is a symbolic link, and calls `process_file` on each remaining path.

4. The script's entry point runs `main()` only when executed directly (guarded by the standard `__name__ == "__main__"` check).

**Error handling and edge cases:**
- Non-integer or negative threshold argument: the current script does not validate it; an implementer should handle a `ValueError` from `int()` gracefully with a usage message to stderr and a nonzero exit code, and reject negative values.
- Symlinks are excluded from size reporting at the `main` level (but symlinked directories are still walked unless `should_skip` excludes them; be careful that the visited-set prevents infinite loops from directory cycles).
- Files that disappear or become unreadable between listing and `stat()` may raise `OSError`; handle these by skipping the file silently or emitting a warning to stderr, and continue scanning.
- Paths outside the cwd cannot occur in normal walking, but `relative_to` would raise `ValueError` if they did; guard against this where practical.
- If the root path is not a directory, the walker yields it as a single item; the cwd is always a directory, so this branch is mainly defensive.
- Files exactly at the threshold are not reported (strict greater-than comparison).
- Zero-byte files and empty directories produce no output.

**Execution and usage:**
- Run from the directory to be scanned: with no arguments to use the 1 MiB default, or with one integer argument giving the threshold in MiB (e.g., `2` for files over 2 MiB).
- Make the script executable with a Termux-compatible shebang line pointing at the Termux Python interpreter.
- Exit with status 0 on normal completion.

**Quality expectations:** Keep the script concise and idiomatic, use type hints consistent with the `from __future__ import annotations` import, use pathlib for path handling, and avoid unnecessary external dependencies.
---"""

from __future__ import annotations

import sys
from pathlib import Path

from dh import fsz


def get_filez(root_dir: str | Path):
    from os import walk as os_walk

    visited_dirs: set[Path] = set()
    root_dir = Path(root_dir)
    if root_dir.is_dir():
        for dirpath, dirnames, filenames in os_walk(root_dir, topdown=True):
            base_path = Path(dirpath)
            for dirname in list(dirnames):
                full_path = base_path / dirname
                resolved_path = full_path.resolve()
                if should_skip(full_path) or resolved_path in visited_dirs:
                    dirnames.remove(dirname)
                visited_dirs.add(resolved_path)
            for filename in filenames:
                path = Path(dirpath) / filename
                if not should_skip(path):
                    yield path
    else:
        yield root_dir


THRESHOLD = 1024 * 1024
cwd = Path.cwd()


def process_file(path: Path, threshold: int = THRESHOLD) -> None:
    sz = path.stat().st_size
    path = Path(path)
    if sz > threshold:
        print(f"{path.relative_to(cwd)} : {fsz(sz)}")


def main() -> None:
    threshold = int(sys.argv[1]) * 1024 * 1024 if len(sys.argv) > 1 else THRESHOLD
    for path in get_filez(cwd):
        if not path.is_symlink():
            process_file(path, threshold)


if __name__ == "__main__":
    raise SystemExit(main())
