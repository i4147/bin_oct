#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory for files, skips binary files, and deletes any text file that is either very short in character count or has very few lines. The script should be a command-line tool that takes no required arguments and operates on the directory it is run from.
Behavior requirements:
- Discover all files in the current working directory using a helper module that provides file listing and binary detection (the tool should rely on these helpers as the source of file discovery and classification).
- For each discovered file, first check whether it is binary. If so, report that the file is binary and leave it untouched.
- For non-binary files, read the content as UTF-8 text. If the file's total character count is below 100 or its number of lines is below 3, delete the file and print a message stating the file name followed by "removed".
- Files that do not exist at processing time should be silently ignored.
- Files that meet or exceed both thresholds must be left unchanged.
- Use the two thresholds (100 characters, 3 lines) as named, easily adjustable constants.
- Print one status line per affected file and no other noisy output.
- The script should exit cleanly when finished, returning a standard exit status, and should only execute its main logic when run directly as a program rather than when imported.
Deliver a robust, readable implementation with sensible handling of edge cases such as empty files and encoding errors, and include brief inline comments explaining the intent of each major step.
---"""

from __future__ import annotations
from pathlib import Path
from dh import get_files, is_binary

SIZE_THRESHOLD = 100
LINE_THRESHOLD = 3


def process_file(path: Path) -> None:
    path = Path(path)
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")
    number_of_lines = len(content.splitlines())
    if len(content) < SIZE_THRESHOLD or number_of_lines < LINE_THRESHOLD:
        del content, number_of_lines
        path.unlink()
        print(f"{path.name} removed")


def main() -> None:
    cwd = Path.cwd()
    files = get_files(cwd)
    for path in files:
        if is_binary(path):
            print(f"{path.name} is binary")
            continue
        process_file(path)


if __name__ == "__main__":
    raise SystemExit(main())
