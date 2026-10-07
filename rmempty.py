#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python 3.12 command-line script designed to run under Termux (shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that finds and deletes empty files in the current working directory tree.

Main behavior and requirements:

- Import `cprint` and `get_files` from a local module named `dh` for colored console output and file enumeration, respectively.
- Define a module-level `TIMEOUT = 0` constant and a helper function `wait_for_keypress(timeout)` that, if `timeout` is greater than 0, flushes stdout and uses `select.select` on `sys.stdin` to wait up to `timeout` seconds for a keypress; if input is detected, it reads a line and returns `True`, otherwise returns `False`. If `timeout <= 0`, it returns `False` immediately without waiting. (This function is defined for potential interactive use but not necessarily called in `main`.)
- Define a `main()` function that:
  - Gets the current working directory via `Path.cwd()`.
  - Retrieves all files in that directory (recursively, via `get_files`).
  - Filters for files whose size is zero bytes, excluding any file named `__init__.py`.
  - If no empty files are found, prints "no empty files found" in cyan using `cprint` and exits with status code 0.
  - If empty files are found, prints the count in cyan (e.g., "`N` empty files found."), then lists each empty file's path (relative to the current working directory) in yellow, prefixed with "    - ".
  - Iterates over the empty files and attempts to delete each one with `unlink()`, checking `exists()` first; counts successful deletions and counts failures (catching any exception during deletion) without raising.
  - Prints a final summary line in green: "Deleted: `<deleted>`, Failed: `<failed>`".
  - Returns `0` from `main()`.
- Use the standard `if __name__ == "__main__": raise SystemExit(main())` pattern to run `main()` and exit with its return code.

Inputs: none required from the user (operates on files in the current directory, discovered via the `dh.get_files` helper).

Outputs: colored console messages reporting the number of empty files found, their relative paths, and a final count of deleted vs. failed deletions. The script exits with code 0 in all normal paths.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/9nr6sDU8oca5SyKVM4Vw7E"""

from __future__ import annotations
import sys
from pathlib import Path
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
