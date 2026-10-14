#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans up the user's shell command history file by removing duplicate entries while preserving the original order of first occurrences. The script should locate the bash history file in the current user's home directory, and if it does not exist, inform the user with a clear message and exit gracefully without making changes. When the file is found, it should read the entire history using lenient text decoding so that malformed bytes do not crash the process, report the total number of entries it contains, and then rewrite the file so that each distinct command appears only once, keeping the earliest occurrence of each and maintaining the original sequence. Comparison between entries should ignore only the trailing newline character, so that otherwise identical commands are treated as duplicates. Finally, the script should report how many lines were removed. Ensure the script runs as a standalone command-line tool with a conventional entry point, returns a clean exit status, and handles the file operations in a way that is safe and easy to understand.
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
