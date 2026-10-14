#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively searches the current working directory and all of its subdirectories for Python wheel files (.whl), moves each one into a single fixed destination folder at /sdcard/whl, creating that folder if it does not already exist. If a file with the same name already exists in the destination, it should be replaced by the incoming file. After each successful move, the original wheel should be removed from its source location so that it no longer remains there. For every file processed, the script should print a short confirmation line showing the original file name and the resulting file name in the destination. When all files have been handled, it should print a final message indicating completion. The script should run as a standalone command-line tool, and if no wheel files are found, it should simply finish quietly with the completion message.
---"""

from __future__ import annotations
from pathlib import Path

if __name__ == "__main__":
    cwd = Path.cwd()
    for path in cwd.rglob("*.whl"):
        fname = path.name
        target_dir = Path("/sdcard/whl")
        if not target_dir.exists():
            target_dir.mkdir(exist_ok=True)
        target_path = target_dir / fname
        if target_path.exists():
            target_path.unlink()
        data = path.read_bytes()
        target_path.write_bytes(data)
        path.unlink()
        print(f"{path.name} -> {target_path.name}")
    print("done")
