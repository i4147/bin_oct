#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a given root directory for license-related files and consolidates their contents into a single combined text file on an Android-style storage path.
The script should:
- Accept a root directory path and walk through all of its subdirectories, skipping version-control metadata folders such as `.git`.
- Identify files whose names contain the word "license" (case-insensitive, covering variants like LICENSE, license.txt, LICENSE-MIT, etc.).
- Ignore the output file itself if it happens to reside within the scanned tree, so it is never read back into itself.
- Gracefully skip directories the process lacks permission to access, and continue processing the rest of the tree without crashing.
- Report to the user how many matching files were found before writing the output.
- Create the destination folder if it does not already exist.
- Write a single UTF-8 text file in which each license file's contents are preceded by a clear header or separator identifying its relative path, so the reader can tell where each file begins and ends.
- Read file contents tolerantly: any undecodable bytes should be ignored rather than causing failure, and files that cannot be read at all should be skipped without stopping the overall run.
- Provide a clear completion message indicating the output location once the consolidated file has been written.
The tool should be a simple, dependable command-line utility that can be run on its own, with the scan root supplied as input and the consolidated text file produced as its sole output.
---"""

from __future__ import annotations
from pathlib import Path

EXCLUDE_DIRS = {".git"}
OUTPUT_FILE = Path("/sdcard/all2.txt")


def read_file(path: Path) -> str | None:
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def collect_files(root: Path):
    try:
        for item in root.iterdir():
            if item.is_dir():
                if item.name not in EXCLUDE_DIRS:
                    yield from collect_files(item)
            elif item.is_file():
                if item.resolve() == OUTPUT_FILE.resolve():
                    continue
                if "license" in item.name.lower():
                    yield item
    except PermissionError:
        pass


def build_all_txt(root_path: str) -> None:
    root = Path(root_path)
    files = list(collect_files(root))
    print(f"Found {len(files)} files")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        for i, path in enumerate(files, 1):
            content = read_file(path)
            if content is None:
                print(f"Skipping unreadable file: {path}")
                continue
            out.write(content)
            if i != len(files):
                out.write("\n\n\n")
            print(f"Added: {path}")
    print(f"\nFinished: {OUTPUT_FILE} created.")


if __name__ == "__main__":
    build_all_txt(".")
