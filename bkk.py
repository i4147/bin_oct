#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively scans the current working directory and all its subdirectories to find files ending with the ".bak" extension.
For each matching file found, print its path relative to the current working directory, then delete the file.
The script should use pathlib's Path.walk() for directory traversal and run its logic under a standard "__main__" guard, requiring no external inputs and producing console output listing the removed backup files as its only result."""

from pathlib import Path

if __name__ == "__main__":
    cwd = Path.cwd()
    for r, _d, files in cwd.walk():
        for file in files:
            path = Path(r) / file
            if path.is_file() and path.name.endswith(".bak"):
                print(path.relative_to(cwd))
                path.unlink()
