#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script that recursively scans the current working directory and reports every regular file modified within the last N minutes, where N is given as the sole command-line argument. Requirements:

**Purpose and behavior**
- Accept one positional argument, `<minutes>`, parsed as an integer. If no argument is given, print the usage line `Usage: python script.py <minutes>` and exit with status 1.
- If the argument is not a valid integer, print `Error: '<value>' is not a valid integer` and exit with status 1.
- If the integer is negative, print `Error: minutes must be a non-negative number` and exit with status 1.
- Zero is valid and means only files modified at the current instant (age ≤ 0 minutes) qualify.
- Use the current working directory as the root (`Path.cwd()`).

**File discovery**
- Recursively enumerate all entries with `rglob("*")`.
- Keep only paths that are regular files, are not symbolic links, and have no path component equal to `.git` (exclude anything inside any `.git` directory).
- If no files are found, print `No files found in current directory` and return normally (exit status 0).

**Age check (per file, run in parallel)**
- For each file, read its modification time via `stat().st_mtime`, compute age in minutes as (current time − mtime) / 60, using `time.time()` as the current time.
- A file qualifies if its age is less than or equal to N minutes.
- For qualifying files, return a tuple of the path as a string and the modification time converted with `datetime.fromtimestamp` (local time).
- Catch `OSError` and `PermissionError` during stat and silently skip that file (return nothing for it). Non-qualifying files also return nothing.
- The per-file function must be a module-level function so it can be pickled by `multiprocessing`. The minutes threshold is shared with workers through a module-level global variable set in `main` (declared `global` there), which works with the default fork start method on Linux/Termux.

**Parallelism**
- Before scanning, print `Checking <count> files for modifications in last <N> minute(s)...` followed by a blank line.
- Use `multiprocessing.Pool(8)` with `pool.map` over all files, then call `close()` and `join()`.
- Filter out `None` results to form the list of recent files.

**Output**
- Print the matching files and their modification timestamps (formatted as a readable local datetime) in the order they were returned, along with a count summary. If no files match, print a message indicating no files were modified within the window.
- Sort or present results clearly; the script should be deterministic in its wording.

**Execution details**
- Begin the file with a Termux-style shebang line: `#!/data/data/com.termux/files/usr/bin/env python`.
- Use `from __future__ import annotations` at the top.
- Guard the entry point with `if __name__ == "__main__":` and call `main()`.
- Use only the Python standard library: `sys`, `time`, `datetime`, `multiprocessing.Pool`, `pathlib.Path`.
- Target Python 3 on Termux (Android), where the pool size of 8 is fixed.

**Edge cases to handle**
- Empty directories or directories containing only `.git` content.
- Files that disappear or become unreadable between enumeration and stat.
- Symbolic links, which must be excluded entirely.
- Very large trees, which are handled by collecting the file list first and mapping over it.
---"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path


def check_file_age(path):
    try:
        mod_time = path.stat().st_mtime
        current_time = time.time()
        age_minutes = (current_time - mod_time) / 60
        if age_minutes <= n_minutes:
            mod_datetime = datetime.fromtimestamp(mod_time)
            return str(path), mod_datetime
    except (OSError, PermissionError):
        pass
    return None


def main():
    global n_minutes
    if len(sys.argv) < 2:
        print("Usage: python script.py <minutes>")
        sys.exit(1)
    try:
        n_minutes = int(sys.argv[1])
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid integer")
        sys.exit(1)
    if n_minutes < 0:
        print("Error: minutes must be a non-negative number")
        sys.exit(1)
    cwd = Path.cwd()
    all_files = [p for p in cwd.rglob("*") if p.is_file() and not p.is_symlink() and ".git" not in p.parts]
    if not all_files:
        print("No files found in current directory")
        return
    print(f"Checking {len(all_files)} files for modifications in last {n_minutes} minute(s)...")
    print()
    pool = Pool(8)
    results = pool.map(check_file_age, all_files)
    pool.close()
    pool.join()
    recent_files = [r for r in results if r is not None]
    recent_files.sort(key=lambda x: x[1], reverse=True)
    if recent_files:
        print(f"Found {len(recent_files)} file(s) modified in the last {n_minutes} minute(s):\n")
        for path, mod_time in recent_files:
            print(f"{mod_time.strftime('%Y-%m-%d %H:%M:%S')} - {Path(path).relative_to(cwd)}")
    else:
        print(f"No files modified in the last {n_minutes} minute(s)")


if __name__ == "__main__":
    raise SystemExit(main())
