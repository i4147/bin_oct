#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans two specific directories in the user's home folder and creates extensionless symbolic links for script files found there, so that each script can be run by a short name. The script should process one directory for shell scripts (files ending in .sh) located in a "bashbin" folder under the home directory, and another directory for Python scripts (files ending in .py) located in a "bin" folder under the home directory. For each matching file, it should create a link in the same directory whose name is the original filename without its extension, pointing to the original file by relative name. If a regular file already occupies the intended link name, it should be replaced with the symbolic link. If a valid symbolic link already exists with that name, it should be left untouched without error. Whenever a new link is created or a conflicting file is replaced, the script should print a concise message showing the link name and the target file name. The script should be safe to run repeatedly, handle missing directories gracefully, and run its processing when executed directly as the main program.
---"""

from __future__ import annotations
from pathlib import Path

BASHBIN: Path = Path.home() / "bashbin"
BIN: Path = Path.home() / "bin"


def process_dir(cwd: Path, ext: str) -> None:
    for path in cwd.glob(f"*.{ext}"):
        path = path.resolve()
        symlink_path = path.with_name(path.stem)
        if symlink_path.exists() and not symlink_path.is_symlink():
            symlink_path.unlink()
            symlink_path.symlink_to(path.name)
            print(f"Created: {symlink_path.name} -> {path.name}")
            continue
        if symlink_path.exists() and symlink_path.is_symlink():
            continue
        if not symlink_path.exists() or not symlink_path.is_symlink():
            symlink_path.symlink_to(path.name)
            print(f"Created: {symlink_path.name} -> {path.name}")


if __name__ == "__main__":
    process_dir(BASHBIN, "sh")
    process_dir(BIN, "py")
