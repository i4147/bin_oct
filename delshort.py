#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python script (intended to run under Termux on Android, using the Termux Python shebang) that scans the current working directory and deletes small text files. Requirements:

Purpose: Clean up the current directory by removing text files that are too small in content, while reporting binary files and leaving them untouched.

Dependencies: Use only the standard library's `pathlib` plus `from __future__ import annotations`. It also imports two helper functions from a local module named `dh`: `get_files(directory)`, which returns an iterable of file paths in the given directory, and `is_binary(path)`, which returns True if the file is binary. Do not reimplement these helpers; import them as-is.

Behavior to reproduce:

1. Start with the shebang line pointing to the Termux Python interpreter path (`/data/data/com.termux/files/usr/bin/env python`).
2. Define two module-level constants: a size threshold of 100 characters and a line threshold of 3 lines.
3. Define `process_file(path)` with a type-annotated `Path` parameter:
   - Convert the argument to a `Path` for safety.
   - If the file does not exist, return silently.
   - Read the file as UTF-8 text.
   - Count lines using `splitlines()`.
   - If the character length of the content is below the size threshold OR the line count is below the line threshold, delete the content and line count variables explicitly, unlink (delete) the file, and print `"<filename> removed"` using only the file's name (not the full path).
   - Otherwise, do nothing.
4. Define `main()`, which takes no arguments and returns None:
   - Get the current working directory via `Path.cwd()`.
   - Retrieve the file list with `get_files(cwd)`.
   - Iterate over each path: if `is_binary(path)` is true, print `"<filename> is binary"` and continue to the next file; otherwise call `process_file(path)`.
5. Under the `if __name__ == "__main__":` guard, call `raise SystemExit(main())`.

Edge cases and error handling: The script performs no explicit try/except blocks, so exceptions (such as UnicodeDecodeError for non-UTF-8 text, or permission errors during unlink) propagate and terminate the script. Files that vanish between listing and processing are silently skipped via the existence check. Empty files and files shorter than the thresholds are deleted. Output is printed to stdout, one line per action.

Usage: Run the script from inside the target directory with no arguments. It operates non-recursively on whatever `get_files` returns for the current directory. The deletion is irreversible, so the reproduction should preserve the exact logic and not add confirmation prompts or dry-run modes unless asked.
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
