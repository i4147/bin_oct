#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line utility that replaces all tab characters with four spaces in one or more text files.
It should accept file and/or directory paths as command-line arguments (recursively collecting non-binary files from directories via a helper), or default to scanning non-binary files in the current working directory when no arguments are given.
For each file, read its content, perform the tab-to-space replacement, and only rewrite the file if the content actually changed, printing a colored status message ("no change" or "updated") using a custom cprint helper.
When processing a single file, exit with status code 1 afterward; when processing multiple files, use a multiprocessing helper (mpf) to process them in parallel."""

from __future__ import annotations

import sys
from pathlib import Path

from dh import cprint, get_nobinary, mpf


def process_file(path: str | Path) -> None:
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    new_content = content.replace("\t", "    ")
    if new_content == content:
        cprint(f"{path.name} (no change)", "grey")
        return
    path.write_text(new_content, encoding="utf-8")
    cprint(f"{path.name} (updated)", "cyan")


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = []
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(get_nobinary(p))
    else:
        files = get_nobinary(cwd)
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
