#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that formats source and markup files in place using an external code formatter. The tool should accept one or more file paths as command-line arguments; if no arguments are given, it should automatically discover all relevant web and documentation files (HTML, HTM, JavaScript, JSX, TypeScript, TSX, Markdown, SCSS, CoffeeScript, and similar variants) within the current working directory. For each candidate file, skip it if it does not exist, is empty, or contains only a single line, since those are not worth formatting. Otherwise, invoke the external formatter in write mode on that file, translating any Android-style storage path prefix into its equivalent shared-storage path before passing it along, and show the formatter's output to the user. Report success or failure per file based on whether the formatter completed without error. When a single file is supplied, process it alone and exit with a failure status code regardless of outcome. When multiple files are supplied, process them concurrently for speed, and ensure the program exits cleanly after all files have been handled. Keep the overall behavior simple, robust against missing files and tool errors, and suitable for running from a terminal on both desktop and mobile Linux environments.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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
