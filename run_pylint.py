#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line lint runner for Python source files. It should accept zero or more file and/or directory paths as command-line arguments. For each file given, it lints that file; for each directory given, it discovers all Python source files within it and lints each of those. If no arguments are provided, it should default to discovering and linting all Python files in the current working directory.
For every Python file targeted, the script should run the pylint static analyzer in a non-persistent, reports-suppressed mode, producing machine-parseable output where each message is formatted as a colon-separated line containing the message category, line number, column, object name, message text, and message identifier. Lint output should be displayed directly to the user as it is produced, and the script should process each file in turn, reporting results for all of them.
The script should be a self-contained utility that relies on a small helper module for file discovery and running external shell commands. It should exit cleanly with a standard process exit status when finished, and it should be runnable directly as a script entry point.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import get_pyfiles, runcmd

CHUNK_SIZE = 1024 * 1024


def process_file(path) -> None:
    path = Path(path)
    cmd = [
        "pylint",
        f"{path!s}",
        "--persistent=n",
        "--reports=n",
        "--output-format=parseable",
        "--msg-template='{C}:{line}:{column}:{obj}:{msg}:{msg_id}'",
        str(path),
    ]
    return runcmd(cmd, show_output=True)


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = []
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            if p.is_dir():
                files.extend(get_pyfiles(p))
    else:
        files = get_pyfiles(cwd)
    for f in files:
        process_file(f)


if __name__ == "__main__":
    raise SystemExit(main())
