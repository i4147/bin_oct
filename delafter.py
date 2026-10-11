#!/data/data/com.termux/files/usr/bin/env python
"""Write a single self-contained Python 3 command-line script (with a Termux-style shebang pointing to `/data/data/com.termux/files/usr/bin/env python`) that uses `from __future__ import annotations` and imports only `sys` and `pathlib.Path`. It takes two positional command-line arguments: first, the path to a text file to be edited in place; second, a single target character or substring used as a cut marker.

Behavior to implement:

- Define a helper that reads a file as UTF-8 text and returns its lines with line endings preserved (use splitlines with keepends=True).
- In the main guard, convert the first argument to a Path, take the second argument as the target string, and initialize an empty output list.
- Iterate over every line read from the file. For each line, strip leading and trailing whitespace.
  - If the stripped line is non-empty and contains the target string, keep only the portion before the first occurrence of the target (use the index of the first match and slice up to it). Append that truncated portion to the output list. Note that this may result in an empty string being appended if the target appears at the very start of the line; preserve that behavior.
  - Otherwise, if the stripped line is non-empty, append the full stripped line.
  - Blank or whitespace-only lines are dropped entirely.
- After processing, if the output list is non-empty, overwrite the original file with all collected entries joined by newline characters (no trailing newline), written in UTF-8. If the output list is empty, leave the file unchanged.

Edge cases and notes to cover:

- The script modifies the input file in place with no backup and no confirmation.
- Lines are stripped of surrounding whitespace, so output lines lose original indentation and trailing newlines.
- Only the first occurrence of the target is used for truncation; the target is treated as a plain substring, not a regex.
- Blank lines are removed from the output.
- No explicit error handling is required beyond what Python naturally raises; missing arguments, a nonexistent file, or encoding errors will surface as standard exceptions. An empty-result file is never overwritten.
- No functions beyond the read helper are needed; keep the script short and idiomatic, matching a simple command-line utility style.

Usage: run as `python <script> <file_path> <target_char>` from a Termux environment or any Python 3 interpreter.
---"""

from __future__ import annotations

import sys
from pathlib import Path


def read_lines(path):
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


if __name__ == "__main__":
    file_name = Path(sys.argv[1])
    nl = []
    target_char = sys.argv[2]
    for line in read_lines(file_name):
        stripped = line.strip()
        if stripped and target_char in stripped:
            indx = stripped.index(target_char)
            cleaned = stripped[:indx]
            nl.append(cleaned)
        elif stripped:
            nl.append(stripped)
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")
