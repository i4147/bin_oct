#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory and all of its subdirectories for backup files (files whose names end with the ".bak" extension). For each backup file found, the script should print its path relative to the starting directory so the user can see what was discovered, and then permanently delete that file. The script should run only when executed directly as a standalone program. Its behavior should be limited to the starting directory tree: it must not modify any files that do not end with ".bak", and it should only act on regular files, skipping directories and other non-file entries. The output should consist of one relative path per deleted file, with no additional decoration required.
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
