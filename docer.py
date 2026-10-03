#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that takes a file path as its single argument and moves that file into a fixed destination folder, /sdcard/doc, creating the folder first if it does not already exist.
The script should read the source file's bytes, write them to a new file of the same name inside /sdcard/doc, then delete the original file, printing "done." on success.
If a file with the same name already exists in the destination folder, it must not overwrite it; instead it should print a message stating the target file exists and instruct the user to remove it and try again, leaving the original file untouched.
The file path should be accessed via sys.argv and handled using pathlib.Path."""

from __future__ import annotations

import sys
from pathlib import Path


def process_file(path) -> None:
    content = path.read_bytes()
    target_dir = Path("/sdcard/doc")
    if not target_dir.exists():
        target_dir.mkdir(exist_ok=True)
    target_path = target_dir / path.name
    if not target_path.exists():
        target_path.write_bytes(content)
        path.unlink()
        print("done.")
    else:
        print(f"target file : {target_path.name} exists. remove it and try again")


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    process_file(fn)
