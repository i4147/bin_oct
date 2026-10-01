#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that runs pylint over one or more targets and prints the results.
It should import helper functions get_pyfiles and runcmd from a local dh module, accept optional file or directory arguments via sys.argv, and if none are given default to scanning all Python files in the current working directory.
For each resolved file, it should build and execute a pylint command with persistent mode and reports disabled, parseable output format, and a custom message template showing category, line, column, object, message, and message ID, streaming the command's output live.
Include a main() entry point invoked through SystemExit for proper exit code handling."""

import sys
from pathlib import Path
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
