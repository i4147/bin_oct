#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that scans two directories, ~/bashbin and ~/bin, for files with .sh and .py extensions respectively, and creates an extensionless symlink in the same directory pointing to each matching file.
For each script, the symlink name should be the file's stem (filename without extension), resolved to the absolute path of the target file.
If a non-symlink file already exists at the target symlink path, the script should delete it and replace it with the symlink; if a symlink already exists there, it should be left untouched; otherwise a new symlink is created.
The script should print a "Created: <symlink_name> -> <target_filename>" message each time a new symlink is created, and run this process for both directories when executed as the main module."""

from __future__ import annotations
from pathlib import Path
import sys


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
