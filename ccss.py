#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python CLI script which minifies CSS files in place using the external `cleancss` tool, with parallel processing, size reporting, and a helper library named `dh` providing utilities.

Build a Python 3 command-line script for Termux (Android) that minifies CSS files in place using the external `cleancss` binary, reporting per-file and total space savings.

**Purpose**
The script optimizes CSS files by running them through the `cleancss` command-line minifier with level-2 optimizations, disabling the `all` optimization group and enabling duplicate-rule removal. It overwrites each file with the minified result and prints a summary of how much disk space was freed.

**Shebang and imports**
- Start with a Termux-specific shebang pointing to the Python interpreter at `/data/data/com.termux/files/usr/bin/env python`.
- Enable postponed annotation evaluation via `from __future__ import annotations`.
- Use the standard library modules `sys` and `pathlib.Path`.
- Import these helpers from a local module named `dh`: `cprint`, `fsz`, `get_files`, `gsz`, `mpf`, and `runcmd`. Assume `dh` already exists; do not reimplement it. Describe the expected behavior of each helper as follows:
  - `gsz(path)`: returns the size in bytes of a file or, for a directory, the total size of its contents.
  - `fsz(n)`: formats a byte count into a human-readable string.
  - `get_files(directory, ext=[...])`: returns a list of files under the directory matching the given extensions.
  - `cprint(text, color)`: prints colored text to the terminal.
  - `runcmd(cmd, show_output=...)`: runs a shell command given as a list and returns a tuple of `(failed_flag, stdout, stderr)`, where a falsy first element means success.
  - `mpf(func, items)`: runs `func` over `items` in parallel (multiprocessing-style map) and returns the results.

**Function: `process_file(path) -> bool`**
1. Convert the input to a `Path`.
2. Record the file's size before processing with `gsz`.
3. If the file does not exist, return `False`.
4. Read the file text; if it contains exactly one line (`splitlines()` length equals 1), return `False` without modifying it. This skips single-line, already-minified files.
5. Print the file's name (not full path) followed by a space, without a trailing newline.
6. Build and run the command: `cleancss -O2 "all:off;removeDuplicateRules:on" <path> -o <path>`, passing each element as a separate list item. Call `runcmd` with `show_output=True`.
7. If the command succeeded (first return value falsy):
   - Record the size after processing and compute `diffsize = before - after`.
   - If `diffsize` is zero, print `[NO CHANGE]` in white.
   - If `diffsize` is nonzero, compute `ratio = after / before * 40` and print `[OK] - <human-readable diffsize> <abs(ratio) with one decimal>%` in cyan. (Note: the ratio formula is intentionally as specified; reproduce it exactly.)
   - Return `True`.
8. If the command failed, print `[ERROR]` in red and return `False`. The error stream output is captured but not used.

**Function: `main() -> None`**
1. Read command-line arguments from `sys.argv[1:]`.
2. Record the current working directory and the total size of the directory before processing.
3. Build the file list: if arguments were given, convert each to a `Path`; otherwise call `get_files` on the current directory with extensions `.css` and `.min.css`.
4. Process all files in parallel by calling `mpf(process_file, files)`; ignore the result.
5. Compute the space freed as the directory size before minus the directory size after.
6. Print `space freed : <human-readable size>` in green.

**Entry point**
Guard execution with `if __name__ == "__main__":` and run `raise SystemExit(main())`.

**Behavior notes and edge cases**
- Files are modified in place; there is no backup.
- Files that are missing or contain only one line are skipped silently (returning `False`).
- Output from the external tool is shown to the terminal during processing (`show_output=True`).
- Per-file output lines may interleave because processing is parallel.
- Type hints use `Path`-compatible inputs; the `process_file` argument may be a string or `Path`.
- The external `cleancss` executable must be installed and on the PATH (e.g., via npm); the script does not check for it explicitly.
- Keep the code concise and idiomatic, with minimal comments, matching a utility script's style.
---"""

from __future__ import annotations

import sys
from pathlib import Path

from dh import cprint, fsz, get_files, gsz, mpf, runcmd


def process_file(path) -> bool:
    path = Path(path)
    before = gsz(path)
    if not path.exists():
        return False
    if len(path.read_text().splitlines()) == 1:
        return False
    print(f"{path.name}", end=" ")
    cmd = [
        "cleancss",
        "-O2",
        "all:off;removeDuplicateRules:on",
        str(path),
        "-o",
        str(path),
    ]
    res, _, _err = runcmd(cmd, show_output=True)
    if not res:
        after = gsz(path)
        diffsize = before - after
        if not diffsize:
            cprint("[NO CHANGE]", "white")
        if diffsize:
            ratio = after / before * 40
            cprint(f"[OK] - {fsz(diffsize)} {abs(ratio):.1f}%", "cyan")
        return True
    cprint("[ERROR]", "red")
    return False


def main() -> None:
    args = sys.argv[1:]
    cwd = Path.cwd()
    before = gsz(cwd)
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".css", ".min.css"])
    _ = mpf(process_file, files)
    diff_size = before - gsz(cwd)
    cprint(f"space freed : {fsz(diff_size)}", "green")


if __name__ == "__main__":
    raise SystemExit(main())
