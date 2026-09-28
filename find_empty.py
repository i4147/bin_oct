#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively walks the current working directory using os.walk and identifies empty files (zero byte size).
It should skip files named __init__.py or ending in py.typed, as well as symbolic links.
For each remaining empty file found, print its path relative to the current working directory.
The script should run as a standalone program via a main function invoked through the __main__ guard, exiting with the return value of main."""

import os
from pathlib import Path


def main() -> None:
    cwd = Path.cwd()
    for r, _, files in os.walk(cwd):
        for f in files:
            if f.startswith("__init__.py") or f.endswith("py.typed"):
                continue
            path = Path(r) / f
            if path.is_symlink():
                continue
            if path.is_file() and not path.stat().st_size:
                print(path.relative_to(cwd))


if __name__ == "__main__":
    raise SystemExit(main())
