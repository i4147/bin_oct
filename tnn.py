#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts tab characters into spaces (four spaces per tab) in text files. The script should accept zero or more command-line arguments, where each argument may be either a file path or a directory path. When a directory is given, the script should process all non-binary files within it. If no arguments are provided, the script should process all non-binary files in the current working directory.
For each file, the script should read its contents as UTF-8 text, replace every tab character with four spaces, and write the result back to the same file only if a change was actually made. It should report the outcome for each file in the console: a neutral or grey-style message when the file had no tabs to replace, and a highlighted (for example, cyan-style) message when the file was updated. Output should show the file name alongside the status.
When exactly one file is found, process it directly. When multiple files are found, process them concurrently or in a parallel-friendly manner so that large batches complete efficiently, while still reporting each file's result. The script should exit with a non-zero status code after handling a single file, and terminate cleanly with a standard exit code when processing multiple files. Handle missing or non-existent arguments gracefully, skip binary files, and ensure that no file is modified unless its content actually contains tab characters.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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
