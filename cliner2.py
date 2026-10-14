#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory and all of its subdirectories for log files, then cleans each one in place by stripping terminal control artifacts and escape-sequence noise from every line. The script should be a standalone command-line tool that requires no arguments and runs from the directory where it is launched.
Key behaviors to cover:
- Discover every file ending in the ".log" extension anywhere beneath the starting directory. If none are found, print a short message stating that no log files were present and exit cleanly.
- Report how many log files were found before processing begins.
- For each log file, read it using UTF-8 encoding, tolerating and silently discarding any bytes that cannot be decoded. Process it line by line.
- Remove a predefined set of terminal-related noise patterns from each line. These include ANSI/VT100 escape sequences for colors, cursor movement, and character set selection; caret-style escape representations; carriage returns; and shift-in/shift-out control characters. Patterns should be matched robustly so that both raw escape bytes and their textual representations are handled.
- After stripping the noise, collapse any run of two or more consecutive spaces into a single space, while leaving single spaces and the rest of the line content intact.
- Overwrite each file with its cleaned content, preserving line structure so that each original line maps to one cleaned line.
- Print a clear success marker with the file path for each file cleaned successfully, and a clear error marker with the file path and the error reason if any file fails. A failure on one file must not stop processing of the remaining files.
- Use the output and file-write encoding of UTF-8 so that non-ASCII text in logs is preserved.
- Keep the tool concise, robust, and safe to run repeatedly: running it twice on the same files should produce the same result.
The output should be a readable console summary of the operations performed, with no interactive prompts.
---"""

from __future__ import annotations
from pathlib import Path
import re

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
