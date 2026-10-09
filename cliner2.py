#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that recursively finds all files with a ".log" extension under the current working directory and cleans them in place by stripping ANSI escape sequences, terminal control codes, carriage returns, and other artifacts like "^[", "^M", "(B", "(0" using a series of regex substitutions, then collapses runs of multiple spaces into a single space.
For each file it should read all lines with UTF-8 encoding (ignoring decode errors), apply the cleaning function line by line, and overwrite the original file with the cleaned content.
It should print progress messages indicating how many log files were found, a checkmark confirmation for each successfully cleaned file, an error message with the exception for any file that fails to process, and a final summary of how many files were processed; if no log files are found it should print a message stating that and exit."""

from __future__ import annotations
from pathlib import Path
import re
import sys


LOG_EXT = ".log"
PATTERNS = [
    r"\^\[",
    r"\[[\dA-Z;]+m",
    r"\[\d+[A-Z]",
    r"\[[\dA-Z;]+",
    r"\^M",
    r"\(B",
    r"\(0",
    r"\x1b\[[0-9;]*[A-Za-z]",
    r"\x1b\([0-9AB]",
    r"\r",
    r"\x0f",
    r"\x0e",
]


def clean_line(line: str) -> str:
    cleaned = line
    for pattern in PATTERNS:
        cleaned = re.sub(pattern, "", cleaned)
    return re.sub(r" {2,}", " ", cleaned)


def clean_file(path: Path) -> None:
    try:
        with Path(path).open(encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        cleaned_lines = [clean_line(line) for line in lines]
        with Path(path).open("w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)
        print(f"✓ Cleaned: {path}")
    except Exception as e:
        print(f"✗ Error processing {path}: {e}")


def main() -> None:
    cwd = Path.cwd()
    log_files = list(cwd.rglob(f"*{LOG_EXT}"))
    if not log_files:
        print(f"No {LOG_EXT} files found.")
        return
    print(f"Found {len(log_files)} log file(s). Cleaning...\n")
    for log_file in log_files:
        clean_file(log_file)
    print(f"\nDone. Processed {len(log_files)} file(s).")


if __name__ == "__main__":
    raise SystemExit(main())
