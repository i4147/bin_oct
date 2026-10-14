#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory (including its subdirectories through whatever file-discovery helper is available) to find all zero-byte files, excluding any file named `__init__.py`. If no empty files are found, the script should print a cyan message stating that no empty files were found and exit cleanly with a success status.
If empty files are found, the script should first report how many were found in cyan, then list each one in yellow using its path relative to the current directory. It should then delete each empty file, keeping a count of successful deletions and failures. Deletion errors for individual files must not stop the script; each failure should be caught and counted so the remaining files are still processed.
After processing, the script should print a summary of how many files were deleted and how many failed, using clear, color-coded console output consistent with the earlier messages.
The script should include an optional keypress-wait feature controlled by a timeout value: when the timeout is greater than zero, it should pause after the summary and wait up to that many seconds for the user to press Enter, and continue immediately if the timeout is zero or negative. The default timeout should be zero so the script runs non-interactively by default. The script should work on Unix-like systems where standard input can be monitored for readiness, and should flush output before waiting.
The script should be runnable directly as a command-line tool, with its main logic executed only when launched as the entry point.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import cprint, get_files

TIMEOUT = 0


def wait_for_keypress(timeout):
    if timeout <= 0:
        return False
    import select

    sys.stdout.flush()
    r, _, _ = select.select([sys.stdin], [], [], timeout)
    if r:
        sys.stdin.readline()
        return True
    return False


def main():
    cwd = Path.cwd()
    files = get_files(cwd)
    empty_files = [p for p in files if p.stat().st_size == 0 and p.name != "__init__.py"]
    found = len(empty_files)
    if not found:
        cprint("no empty files found", "cyan")
        sys.exit(0)
    cprint(f"{found} empty files found.", "cyan")
    for empty_file in empty_files:
        cprint(f"    - {empty_file.relative_to(cwd)}", "yellow")
    deleted = 0
    failed = 0
    for empty_file in empty_files:
        try:
            if empty_file.exists():
                empty_file.unlink()
                deleted += 1
        except Exception as e:
            failed += 1
    cprint(f"Deleted: {deleted}, Failed: {failed}", "green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
