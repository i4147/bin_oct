#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 script for a Termux environment (shebang pointing to the Termux Python path) that deduplicates the user's bash history file.

Purpose: Remove duplicate command lines from the user's bash history file, keeping the first occurrence of each distinct line and preserving original order.

Requirements:
- Use `from __future__ import annotations` and `pathlib.Path`.
- Target file: `.bash_history` located in the user's home directory (resolved via `Path.home()`).
- If the file does not exist, print exactly `~/.bash_history does not exist.` and return without error.
- Open the file for reading with UTF-8 encoding, using `errors="ignore"` to skip undecodable bytes. Read all lines with `readlines()`.
- Print the total number of original lines in the format `history length: N`.
- Deduplicate by comparing each line with its trailing newline (`\\n` only) stripped. Keep the first occurrence of each stripped value, and keep the original line (including its newline) in the output list. Preserve order. Empty lines are treated as ordinary values and deduplicated the same way.
- Overwrite the same file in write mode with UTF-8 encoding, writing only the retained lines via `writelines`.
- Print the number of removed lines in the format `N lines removed`, where N is original count minus retained count.
- Structure the code in a `main()` function returning `None`, and invoke it under an `if __name__ == "__main__":` guard using `raise SystemExit(main())`.
- Use only the Python standard library; no third-party dependencies.
- No command-line arguments, no prompts, no backup file creation, and no confirmation step. The file is modified in place immediately.
- Error handling: the script does not add explicit try/except blocks; permission errors or I/O failures propagate as standard exceptions. Note that the file is truncated before the write completes, so an interruption during writing could lose data.
- Edge cases: an empty history file yields `history length: 0` and `0 lines removed`; lines without trailing newlines are matched correctly; the last line may lack a newline and is preserved as-is.
- Usage: run directly under Termux (`python3 script.py`) or as an executable with the Termux shebang; it operates only on the invoking user's home directory.
- Output only the script itself with a brief docstring or comments as appropriate, nothing else.
---"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    hist_file = Path.home() / ".bash_history"
    if not hist_file.exists():
        print("~/.bash_history does not exist.")
        return
    with hist_file.open("r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    seen = set()
    unique_lines = []
    histlen = len(lines)
    print(f"history length: {histlen}")
    for line in lines:
        stripped = line.rstrip("\n")
        if stripped not in seen:
            seen.add(stripped)
            unique_lines.append(line)
    with hist_file.open("w", encoding="utf-8") as f:
        f.writelines(unique_lines)
    print(f"{histlen - len(unique_lines)} lines removed")


if __name__ == "__main__":
    raise SystemExit(main())
