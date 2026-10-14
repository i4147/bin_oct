#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a specified source directory on an Android device's shared storage, identifies the single largest regly inside that directory (ignoring subdirectories), and copies its contents to a new file in a public downloads folder. The destination filename should be a randomly generated lowercase alphanumeric-letter name of a fixed short length with a video container extension. After copying, the script should print the destination file's name along with the size of the copied file in megabytes. If the source directory contains no regular files, the script should complete without creating a destination file or printing output. The script should run as a standalone command-line program with the source and destination locations hardcoded to the described Android paths.
---"""

from __future__ import annotations
from pathlib import Path


def copy_largest_file(source_dir, dest):
    largest = None
    max = -1
    for path in source_dir.iterdir():
        if path.is_file():
            size = path.stat().st_size
            if size > max:
                max = size
                largest = path
    if largest:
        dest.write_bytes(largest.read_bytes())
        print(f"{dest.name} ({max / (1024 * 1024)} MB)")


def get_random_filename(length: int = 6) -> str:
    from random import choice
    from string import ascii_lowercase

    letters: str = ascii_lowercase
    return "".join(choice(letters) for _ in range(length))


if __name__ == "__main__":
    source = Path("/sdcard/Android/data/org.telegram.messenger/cache")
    dest = Path(f"/sdcard/Download/{get_random_filename()}.mkv")
    copy_largest_file(source, dest)
