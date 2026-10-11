#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python command-line script with the following specification:

Create a single-file Python 3 command-line utility named along the lines of a "dangling symlink cleaner." Its purpose is to walk the current working directory recursively and find symbolic links whose targets no longer exist (broken or dangling symlinks), then either delete them or, in dry-run mode, report them.

Requirements to implement:

- Begin with a Termux-specific shebang line pointing to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/env python`. Include `from __future__ import annotations` at the top, and use only the standard library (`sys` and `pathlib`).
- Operate on the current working directory only (determined via `Path.cwd()` at runtime). No other input paths or config files are needed.
- Recursively traverse the directory tree using `Path.walk()`, which yields `(root, dirs, files)` tuples. Only examine the `files` lists; ignore the directory list.
- Skip any path that contains a `.git` component anywhere in its path parts, so that Git metadata is never touched.
- For each file entry, build its full path by joining the root with the filename. Treat an entry as a target only when it is a symbolic link AND it does not resolve to an existing path (i.e., it is a dangling symlink). Regular files and valid symlinks must be left alone.
- Behavior depends on command-line arguments, detected by checking whether the literal string `-d` appears anywhere in `sys.argv`:
  - Without `-d`: delete each dangling symlink with `unlink()` and print a line in the format ` - <filename> removed.` (using only the bare filename, not the full path, with a leading space and hyphen).
  - With `-d`: do not delete anything. Print ` - <filename> (rerun without -d to remove` for each dangling symlink found. Note that this message has an unclosed parenthesis as written; reproduce it exactly as specified.
- The script should not print anything for files that are not dangling symlinks.
- Structure the code with a `blink(directory: Path) -> None` function that performs the traversal and action, and a `main()` function that obtains the current directory and calls `blink`. The entry point should be guarded by `if __name__ == "__main__":` and should call `raise SystemExit(main())`.
- Error handling: the script does not add explicit try/except blocks. Permission errors or race conditions during `unlink()` will propagate as uncaught exceptions. Reproduce this minimal behavior unless otherwise noted.
- Edge cases to preserve: symlinks inside `.git` directories are ignored; dangling symlinks in nested subdirectories are processed; a filename that appears in multiple directories will be reported once per occurrence; the `-d` flag is matched anywhere in arguments, not just as the first argument; no arguments beyond `-d` are recognized.
- Usage: run from inside the target directory with `python <script>` to delete dangling symlinks, or `python <script> -d` to preview them without removing anything. Exit status comes from `main()` returning None, which yields a normal exit code of 0.
- Keep the implementation concise, with no docstrings beyond what is needed and no third-party dependencies.
---"""

from __future__ import annotations

import sys
from pathlib import Path


def blink(directory: Path) -> None:
    for root, _, files in directory.walk():
        for f in files:
            fullpath = Path(root) / f
            if ".git" in fullpath.parts:
                continue
            if fullpath.is_symlink() and not fullpath.exists():
                if "-d" not in sys.argv:
                    fullpath.unlink()
                    print(f" - {f} removed.")
                else:
                    print(f" - {f} (rerun without -d to remove")


def main():
    cwd = Path.cwd()
    blink(cwd)


if __name__ == "__main__":
    raise SystemExit(main())
