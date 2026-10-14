#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path from the command line, moves that file into a fixed central documents folder on an Android-style storage location, creating the folder if it does not already exist. The script should copy the file's contents into that folder under the same filename, then remove the original file only after the copy succeeds. If a file with the same name already exists in the destination, the script must not overwrite it or delete the source; instead, it should report to the user that the target file already exists and ask them to remove it and retry. On successful transfer, the script should print a short confirmation message. Handle the case where the input path is missing or invalid by reporting a clear error to the user rather than crashing with an unhandled traceback.
---"""

from __future__ import annotations
from pathlib import Path
import sys


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
