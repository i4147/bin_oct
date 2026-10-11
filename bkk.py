#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 script that deletes backup files from the current directory tree. Requirements:

- Shebang line pointing to the Termux Python interpreter at /data/data/com.termux/files/usr/bin/env python, and begin the file with `from __future__ import annotations`.
- Use only the standard library: `pathlib.Path`. No third-party dependencies.
- Run all logic under an `if __name__ == "__main__":` guard so the file is safe to import.
- Start from the current working directory (`Path.cwd()`), resolved at runtime, not hardcoded.
- Recursively traverse the entire directory tree beneath it using `Path.walk()`, which yields a (root, directories, files) tuple per directory. Ignore the directory list; only the file list matters.
- For each file name in each visited directory, build the full path by joining the root and file name. Process it only if it is a regular file (not a symlink to a directory or a directory itself) and its name ends with the exact suffix `.bak` (case-sensitive; files like `.BAK` or `.bak.txt` are not matched).
- For each matching file, first print its path relative to the starting directory (so the output shows only the relative path, one per line, printed to standard output), then delete the file with `unlink()`.
- Do not add confirmation prompts, dry-run mode, command-line arguments, logging to files, or any other options; the behavior is unconditional and immediate.
- Do not catch or handle exceptions: if a deletion fails (for example, due to permissions), let the exception propagate and terminate the script with a traceback.
- Do not follow symbolic links into other directories beyond what `Path.walk()` does by default, and do not delete directories, even if their names end in `.bak`.
- Edge cases: an empty directory tree or no matching files should produce no output and exit normally with status 0. Files are printed before they are removed, so a failure on one file leaves earlier matches already deleted and reported.
- Keep the script short and idiomatic, with no comments beyond what is needed for clarity, and no output other than the relative paths of deleted files.
---"""

from __future__ import annotations

from pathlib import Path

if __name__ == "__main__":
    cwd = Path.cwd()
    for r, _d, files in cwd.walk():
        for file in files:
            path = Path(r) / file
            if path.is_file() and path.name.endswith(".bak"):
                print(path.relative_to(cwd))
                path.unlink()
