#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively finds all files with a given log extension under a directory, then cleans each file in place by stripping ANSI/terminal escape sequences, carriage returns, and other control characters (using a set of precompiled regex patterns), and collapsing multiple consecutive spaces into one.
It should choose between two cleaning strategies based on file size: read small files normally with readlines/writelines, but use memory-mapped file I/O (mmap) for files exceeding a defined size threshold (1MB) to handle large files efficiently.
The script should process files concurrently using a worker pool (e.g., 4 workers), and each cleaning function should return a tuple indicating the file path, success status, and a message describing the outcome or any error encountered."""

from __future__ import annotations

import mmap
import re
from pathlib import Path

from dh import mpf

LOG_EXT = ".log"
MMAP_THRESHOLD = 1 * 1024 * 1024
NUM_WORKERS = 4
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
COMPILED_PATTERNS = [re.compile(pattern) for pattern in PATTERNS]


def clean_line(line: str) -> str:
    cleaned = line
    for pattern in COMPILED_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    return re.sub(" {2,}", " ", cleaned)


def clean_file_small(path: Path) -> tuple:
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        cleaned_lines = [clean_line(line) for line in lines]
        with path.open("w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)
        return (path, True, "small file")
    except Exception as e:
        return (path, False, str(e))


def clean_file_large(path: Path) -> tuple:
    try:
        with path.open("r+b") as f:
            get_size = f.seek(0, 2)
            f.seek(0)
            if get_size == 0:
                return (path, True, "empty file")
            with mmap.mmap(f.fileno(), 0) as mmapped_file:
                content = mmapped_file.read().decode("utf-8", errors="ignore")
        lines = content.splitlines(keepends=True)
        cleaned_lines = [clean_line(line) for line in lines]
        cleaned_content = "".join(cleaned_lines)
        Path(path).write_text(cleaned_content, encoding="utf-8")
        return (path, True, "large file (mmap)")
    except Exception as e:
        return (path, False, str(e))


def clean_file_worker(path: Path) -> tuple:
    try:
        get_size = path.stat().st_size
        if get_size > MMAP_THRESHOLD:
            return clean_file_large(path)
        return clean_file_small(path)
    except Exception as e:
        return (path, False, str(e))


def main() -> None:
    cwd = Path.cwd()
    log_files = list(cwd.rglob(f"*{LOG_EXT}"))
    if not log_files:
        print(f"No {LOG_EXT} files found.")
        return
    print(f"Found {len(log_files)} log file(s).")
    results = mpf(clean_file_worker, log_files)
    success_count = 0
    error_count = 0
    for path, success, message in results:
        if success:
            print(f"✓ Cleaned: {path} ({message})")
            success_count += 1
        else:
            print(f"✗ Error: {path} - {message}")
            error_count += 1
    print(f"\nDone. Successfully processed {success_count}/{len(log_files)} file(s).")
    if error_count > 0:
        print(f"Failed: {error_count} file(s).")


if __name__ == "__main__":
    raise SystemExit(main())
