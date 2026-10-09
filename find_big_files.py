#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that recursively scans the current working directory (or a single given path) for files larger than a size threshold and prints each qualifying file's path (relative to the current directory) along with its human-readable size, using a helper `fsz` function from a local `dh` module for formatting.
The threshold defaults to 1MB but can be overridden by passing a number of megabytes as the first command-line argument.
The script should walk directories using `os.walk`, skip symlinked files/directories and any paths matched by a `should_skip` filter function, and avoid revisiting already-processed directories by tracking their resolved paths in a set.
It should be structured with a generator function to yield candidate file paths and a separate function to check and report oversized files, executed via a `main()` entry point."""

from __future__ import annotations
from pathlib import Path
import sys

from dh import fsz


def get_filez(root_dir: str | Path):
    from os import walk as os_walk

    visited_dirs: set[Path] = set()
    root_dir = Path(root_dir)
    if root_dir.is_dir():
        for dirpath, dirnames, filenames in os_walk(root_dir, topdown=True):
            base_path = Path(dirpath)
            for dirname in list(dirnames):
                full_path = base_path / dirname
                resolved_path = full_path.resolve()
                if should_skip(full_path) or resolved_path in visited_dirs:
                    dirnames.remove(dirname)
                visited_dirs.add(resolved_path)
            for filename in filenames:
                path = Path(dirpath) / filename
                if not should_skip(path):
                    yield path
    else:
        yield root_dir


THRESHOLD = 1024 * 1024
cwd = Path.cwd()


def process_file(path: Path, threshold: int = THRESHOLD) -> None:
    sz = path.stat().st_size
    path = Path(path)
    if sz > threshold:
        print(f"{path.relative_to(cwd)} : {fsz(sz)}")


def main() -> None:
    threshold = int(sys.argv[1]) * 1024 * 1024 if len(sys.argv) > 1 else THRESHOLD
    for path in get_filez(cwd):
        if not path.is_symlink():
            process_file(path, threshold)


if __name__ == "__main__":
    raise SystemExit(main())
