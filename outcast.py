#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans a given source directory (defaulting to the Telegram app's cache folder on Android, `/sdcard/Android/data/org.telegram.messenger/cache`), finds the single largest file within it by size, and copies its contents to a destination file.
The destination file should be placed in `/sdcard/Download/` and named with a random 6-letter lowercase string plus a `.mkv` extension, generated via a helper function.
After copying, the script should print the destination filename along with the copied file's size in megabytes.
The copy should be performed by reading all bytes from the largest file and writing them to the destination path."""

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
