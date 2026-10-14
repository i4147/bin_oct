#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory tree for license files and clears their contents. The script should recursively discover all regular files (skipping symbolic links), identify those whose base name begins with "license" (case-insensitive) and whose extension is either one of `.md`, `.txt`, `.rst`, or absent entirely. For each matching file, print the file's base name and extension as it is processed, then print a summary line stating how many license files were found. Finally, overwrite every matched file with empty content encoded as UTF-8, effectively truncating each license file to zero bytes. The script should run as a standalone command-line tool with its main logic executed only when launched directly. Prioritize correctness and safety, ensuring that non-matching files and symbolic links are left untouched.
---"""

from __future__ import annotations
from pathlib import Path
import dh

EXT = [".md", ".txt", ".rst"]


def find_license_files() -> None:
    lf = []
    allfiles = dh.get_files(".")
    for file in allfiles:
        if Path(file).is_symlink():
            continue
        if Path(file).is_file():
            fn = str(dh.get_fname(file))
            ext = str(dh.get_ext(file))
            if fn.lower().startswith("license") and (ext.lower() in EXT or not ext):
                print(fn, ext)
                lf.append(file)
    print(f"Found {len(lf)} license files")
    for path in lf:
        Path(path).write_text("", encoding="utf-8")


if __name__ == "__main__":
    find_license_files()
