#!/data/data/com.termux/files/usr/bin/env python
"""You are writing a prompt for an AI coding agent. Its job is to produce a Python script that reproduces the behavior described below. Write the script to run under Termux on Android, using the Python 3 standard library plus one helper module.

The script is a command-line tool that recursively counts files with a given extension under the current working directory and reports their combined size in human-readable form.

**Inputs:**
- One required positional command-line argument: a file extension. A leading dot is optional and must be stripped before use (for example, both "py" and ".py" are treated as "py").
- No other flags, options, or environment variables.
- The search root is the process's current working directory at launch time.

**Behavior:**
1. If no extension argument is provided, print a two-line usage message to standard output: a usage line showing the form `script.py <extension>`, and an example line showing `script.py py`. Then exit with status code 1.
2. Recursively search the current directory and all subdirectories for files whose names end with `.<ext>`. Use the pathlib recursive glob pattern for this. The match is case-sensitive as the pattern is applied, and the search includes only regular matches returned by the glob (directories with matching names are included in the glob results, so the implementation should ensure they are counted only if they are files, or accept the glob behavior consistently and document it in a code comment).
3. If no matching files are found, print a message in the form "No .<ext> files found in current directory" and exit with status code 0.
4. Otherwise, compute:
   - The count of matching files.
   - The total size in bytes, obtained by summing the size reported by each file's stat information.
5. Print two lines to standard output:
   - `Total number of .<ext> files: <count>`
   - `Total size of .<ext> files: <formatted size>`
   The formatted size must come from a helper function named `fsz` imported from a module named `dh`. Treat `fsz` as an existing function that accepts a byte count and returns a human-readable string. Do not reimplement it.

**Structure and conventions:**
- Include a Termux-specific shebang line pointing to the Termux Python interpreter path.
- Use `from __future__ import annotations` at the top.
- Put the logic in a `main()` function that returns `None`, and guard the entry point with the standard `if __name__ == "__main__":` check, which raises `SystemExit` with the return value of `main()`.
- Use `sys` for argument access and exit codes, and `pathlib.Path` for filesystem work.
- Keep the script short, with no extra dependencies beyond the standard library and `dh`.

**Edge cases and error handling:**
- Extension arguments with leading dots must be normalized.
- Empty matches must exit cleanly with status 0, not an error.
- The script does not explicitly handle permission errors, broken symlinks, or files that disappear during the scan; allow those exceptions to propagate unless the implementer deems otherwise, and note the choice in a comment.
- Symlinks are followed or not according to pathlib's default `rglob` behavior; do not add custom symlink handling.
- Output goes to standard output only; no logging framework is needed.

**Execution:** Run the script from inside the target directory, for example `script.py py` to report all Python files beneath the current folder, or `script.py .txt` to report text files.
---"""

from __future__ import annotations

import sys
from pathlib import Path

from dh import fsz


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: script.py <extension>")
        print("Example: script.py py")
        sys.exit(1)
    ext = sys.argv[1].lstrip(".")
    cwd = Path.cwd()
    files = list(cwd.rglob(f"*.{ext}"))
    if not files:
        print(f"No .{ext} files found in current directory")
        sys.exit(0)
    total_size = sum(f.stat().st_size for f in files)
    count = len(files)
    print(f"Total number of .{ext} files: {count}")
    print(f"Total size of .{ext} files: {fsz(total_size)}")


if __name__ == "__main__":
    raise SystemExit(main())
