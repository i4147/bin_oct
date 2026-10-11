#!/data/data/com.termux/files/usr/bin/env python
"""Write a single self-contained Python script (targeting Termux on Android, Python 3 with `from __future__ import annotations` for type hints) that does the following:

Purpose: Locate the largest regular file in a fixed source directory on Android shared storage (the Telegram Android app's cache folder, `/sdcard/Android/data/org.telegram.messenger/cache`), copy its contents into a newly named file in `/sdcard/Download/`, and print a summary of the copied file's name and size.

Requirements:

1. Use the `pathlib` module for all filesystem paths and operations. Do not use `shutil` or `os.path` for the copy.

2. Define a function `copy_largest_file(source_dir, dest)` that:
   - Iterates over the immediate children of `source_dir` (non-recursive) using `iterdir()`.
   - Considers only entries where `is_file()` is true; skips directories, symlinks to directories, and other non-files.
   - Obtains each file's size via `stat().st_size`.
   - Tracks the file with the greatest size, starting from an initial maximum of -1 so that zero-byte files can still be selected as a candidate.
   - If a largest file was found, reads its full contents into memory with `read_bytes()` and writes them to `dest` with `write_bytes()`, overwriting `dest` if it exists.
   - Prints a single line in the format: the destination file's name, a space, an opening parenthesis, the size in bytes divided by (1024 × 1024) as a float, the text " MB", and a closing parenthesis. Example shape: `abcdef.mkv (12.345678 MB)`.
   - If no regular files are found (or the directory is empty), it does nothing and prints nothing.

3. Define a function `get_random_filename(length: int = 6) -> str` that:
   - Imports `choice` from `random` and `ascii_lowercase` from `string` inside the function body (local imports).
   - Returns a string of `length` characters, each chosen independently and uniformly at random from the lowercase ASCII letters a–z.
   - Uses a type-annotated local variable for the alphabet.

4. Main entry point, guarded by `if __name__ == "__main__":`:
   - Set `source` to a `Path` for `/sdcard/Android/data/org.telegram.messenger/cache`.
   - Set `dest` to a `Path` formed as `/sdcard/Download/` followed by a random 6-letter name from `get_random_filename()` plus the `.mkv` extension.
   - Call `copy_largest_file(source, dest)`.

5. Script header: begin with the shebang line `#!/data/data/com.termux/files/usr/bin/env python`, followed by a blank line and `from __future__ import annotations`, then `from pathlib import Path`.

6. Error handling and edge cases to preserve as behavior: the script does not catch exceptions, so a missing source directory, permission errors on `/sdcard` (common on Android without storage permission granted via `termux-setup-storage`), or write failures will raise uncaught exceptions. Ties in size keep the first file encountered in iteration order. Files are read fully into memory, so very large files may consume significant RAM. The output filename is random, so repeated runs produce different destinations, and existing files at the destination are overwritten only in the unlikely event of a name collision.

7. Usage: run directly with the Termux Python interpreter (e.g., `python script.py`) from Termux after granting storage access. No command-line arguments are accepted; all paths are hard-coded. No third-party dependencies are required; only the Python standard library is used.

8. Style: concise, idiomatic, with minimal comments and a single blank line between top-level definitions as appropriate for a small utility script.
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
