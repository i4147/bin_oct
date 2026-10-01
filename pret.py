#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that formats source files using Prettier.
It should accept file paths as command-line arguments, or if none are given, recursively discover files in the current directory matching extensions like .html, .js, .jsx, .ts, .tsx, .md, .scss, and .coffee via a helper `get_files`.
For each file, skip it if it doesn't exist, is empty, or has only one line; otherwise run `prettier -w` on it, adjusting the path prefix from "/storage/emulated/0" to "/sdcard" for Android compatibility, and return a success/failure flag with the file path.
Process a single file directly, or use a multiprocessing helper `mpf` to format multiple files in parallel, relying on utility functions imported from a local `dh` module."""

import sys
from pathlib import Path
from dh import get_files, mpf, runcmd


def process_file(path: str | Path) -> tuple[bool, Path]:
    path = Path(path)
    if not path.exists() or not path.stat().st_size:
        return (False, path)
    if sum(1 for _ in path.open()) == 1:
        return (False, path)
    ret = runcmd(
        ["prettier", "-w", str(path).replace("/storage/emulated/0", "/sdcard")],
        show_output=True,
    )
    if not ret:
        return (True, path)
    return (False, path)


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = (
        [Path(f) for f in args]
        if args
        else get_files(
            cwd,
            e=[
                ".html",
                ".htm",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".md",
                ".jsm",
                ".scss",
                ".tsm",
                ".coffee",
            ],
        )
    )
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
