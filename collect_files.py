#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory and all of its subdirectories for files with a user-specified extension (for example, "txt", "pdf", or "jpg"), and gathers copies of every matching file into a single new folder named after that extension, created inside the current working directory if it does not already exist.
The script should accept the target file extension as a command-line argument and handle missing or malformed input gracefully with a clear usage message. It should skip any files that already reside inside the destination folder so they are not copied into themselves, and it should preserve file metadata such as timestamps when copying.
Where two source files share the same name, the script must not overwrite existing files in the destination; instead, it should generate a unique name by appending an incrementing numeric suffix before the extension. Each successful copy should be reported to the user with a message showing the original path and the new destination path. If an individual file fails to copy (for example, due to permission errors), the script should report the problem for that file and continue processing the remaining files rather than stopping entirely.
At completion, the script should print a summary indicating how many files were successfully copied. The tool should be safe, non-destructive to original files, and suitable for use in any directory tree on a standard desktop operating system.
---"""

from __future__ import annotations
from pathlib import Path
import shutil
import sys


def unique_destination_path(dest_dir: Path, filename: str) -> Path:
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def collect_files_by_extension(extension: str) -> None:
    cwd = Path.cwd()
    target_dir = cwd / extension
    target_dir.mkdir(parents=True, exist_ok=True)
    copied_count = 0
    for path in cwd.rglob(f"*.{extension}"):
        if path.is_file() and target_dir not in path.parents:
            try:
                destination_path = unique_destination_path(target_dir, path.name)
                shutil.copy2(path, destination_path)
                print(f"Copied: {path} -> {destination_path}")
                copied_count += 1
            except Exception as e:
                print(f"Error copying {path}: {e}")
    print("\nFinished collecting files.")
    print(f"Total files copied: {copied_count}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python collect_files.py <extension>")
        sys.exit(1)
    file_extension = sys.argv[1].lower().strip(".")
    collect_files_by_extension(file_extension)
