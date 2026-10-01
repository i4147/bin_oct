#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans files for multiple shebang lines.
It should import a helper function get_files from a local module named dh to gather file paths: if command-line arguments are provided, treat each as a file to add directly or a directory to recursively search, otherwise default to scanning all ".py" files in the current working directory.
For each collected file, skip it if it's a symlink, otherwise read its content, count lines starting with "#!", and print the file's name if more than one such line is found."""

import sys
from pathlib import Path
from dh import get_files


def process_file(path: Path) -> None:
    path = Path(path)
    if path.is_symlink():
        return
    content = path.read_text()
    lines = content.splitlines()
    c = 0
    for line in lines:
        if line.startswith("#!"):
            c += 1
    if c > 1:
        print(path.name)


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            if p.is_dir():
                files.extend(get_files(p))
    else:
        files = get_files(cwd, ext=[".py"])
    for f in files:
        process_file(f)


if __name__ == "__main__":
    raise SystemExit(main())
