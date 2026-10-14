#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file or directory path from the command line, resolves it to an absolute location, and moves it into a "repos" folder located in the current user's home directory. The destination folder should keep the original item's name. If an item with that name already exists there, the script should generate a unique alternative name instead of overwriting anything. Once the move completes, the script should print a short confirmation showing the original name and the final name it was saved under, in the form "original_name --> final_name". Use the helper function `unique_path` from a module named `dh` to produce non-conflicting names. The script should run only when executed directly, not when imported.
---"""

from __future__ import annotations
from pathlib import Path
import shutil
import sys
from dh import unique_path

if __name__ == "__main__":
    src = Path(sys.argv[1]).resolve()
    cwd = Path.home() / "repos"
    dst = cwd / src.name
    if dst.exists():
        dst = unique_path(dst)
    shutil.move(str(src), str(dst))
    print(f"{src.name} --> {dst.name}")
