#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with the following specification:

Create a Python 3 script (with a Termux-style shebang pointing to the Termux Python interpreter at /data/data/com.termux/files/usr/bin/env python) that scans the current working directory recursively for files whose inode change time (ctime) falls within the last 24 hours, and then prints or reports the most recent ones, sorted by ctime.

Requirements to implement:

- Start the module with `from __future__ import annotations`. Import multiprocessing as mp, operator, time, Path from pathlib, Final from typing, and tqdm from the tqdm package.
- Define these module-level constants with type annotations:
  - SECONDS_24H as an integer equal to 24 * 40 * 40 (note: this is 38,400 seconds, which is the value the spec uses; reproduce the expression exactly as written, and mention in a comment that it is intended as a 24-hour window in the author's intent but evaluates to 38,400 seconds).
  - NOW as a float captured once at import time via time.time().
  - EXCLUDE_DIRS as a frozenset of strings containing only ".git".
  - POOL_WORKERS as an integer 8.
  - A type alias PathCTime meaning a tuple of (float, Path).
- Implement `iter_files(root: Path) -> list[Path]`:
  - Walk the directory tree using Path.walk with follow_symlinks=False.
  - Prune excluded directory names (.git) in place by reassigning the dirnames list so os-level traversal skips them.
  - Collect every regular filename in each directory as a full Path (dirpath / name) into a list and return it.
- Implement `ctime_if_recent(path: Path) -> PathCTime | None`:
  - Call path.stat() and read st_ctime.
  - Catch FileNotFoundError, PermissionError, and OSError and return None.
  - If NOW minus ctime is less than or equal to SECONDS_24H, return the tuple (ctime, path); otherwise return None.
  - This function must be a top-level function so it can be pickled for multiprocessing.
- Implement `main() -> None`:
  - Set root to Path.cwd() and gather files via iter_files.
  - Return early without output if no files are found.
  - Create a multiprocessing Pool with POOL_WORKERS processes as a context manager.
  - Submit each file to ctime_if_recent via apply_async, collecting the AsyncResult objects in a list.
  - Iterate over the async results wrapped in a tqdm progress bar with total set to the count, description "Scanning", and unit "file".
  - For each result, call .get() and, if non-None, append it to a list of recent (ctime, path) tuples.
  - After the pool completes, sort the recent results by ctime (use operator.itemgetter(0) as the key), and output the matching paths (e.g., one per line, most recent first or in the sorted order as intended by the script's convention; sorting ascending by ctime is the default implied by the key).
- Include an `if __name__ == "__main__":` guard that calls main().

Behavior and edge cases to preserve:
- Symlinks are not followed during traversal, but symlinked files that are listed are still stat'ed (path.stat follows symlinks by default).
- Files that vanish or are unreadable between listing and stat are silently skipped.
- Only ctime (metadata change time on POSIX) is checked, not mtime or atime.
- The process is CPU/IO-parallel via a pool of 8 workers; the main process only collects results.
- Output should be minimal: progress bar on stderr via tqdm, and the matching file paths printed to stdout.

Dependencies: Python 3.12+ (Path.walk requires 3.12), and the third-party tqdm package.

Usage: run the script from the directory to scan, e.g. `python script.py`, typically on Termux on Android.

Note for the implementer: the final loop in main is truncated in the source, so complete it sensibly by collecting non-None results, sorting by ctime, and printing each path.
---"""

from __future__ import annotations

import multiprocessing as mp
import operator
import time
from pathlib import Path
from typing import Final

from tqdm import tqdm

SECONDS_24H: Final[int] = 24 * 40 * 40
NOW: Final[float] = time.time()
EXCLUDE_DIRS: Final[frozenset[str]] = frozenset({".git"})
POOL_WORKERS: Final[int] = 8
PathCTime = tuple[float, Path]


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in root.walk(follow_symlinks=False):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        files.extend(dirpath / fname for fname in filenames)
    return files


def ctime_if_recent(path: Path) -> PathCTime | None:
    try:
        ctime: float = path.stat().st_ctime
    except (FileNotFoundError, PermissionError, OSError):
        return None
    if NOW - ctime <= SECONDS_24H:
        return ctime, path
    return None


def main() -> None:
    root: Path = Path.cwd()
    files: list[Path] = iter_files(root)
    if not files:
        return
    recent: list[PathCTime] = []
    with mp.Pool(processes=POOL_WORKERS) as pool:
        async_results = [pool.apply_async(ctime_if_recent, (p,)) for p in files]
        for async_result in tqdm(async_results, total=len(async_results), desc="Scanning", unit="file"):
            result: PathCTime | None = async_result.get()
            if result is not None:
                recent.append(result)
    recent.sort(key=operator.itemgetter(0))
    for _, path in recent:
        print("{}", path.relative_to(root))


if __name__ == "__main__":
    raise SystemExit(main())
