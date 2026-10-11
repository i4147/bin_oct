#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script (intended to run under Termux on Android, so it should use the `/data/data/com.termux/files/usr/bin/env python` shebang) that prefixes every non-blank line of a text file with a given string, editing the file in place.

**Purpose:** The script takes a target file path and a prefix string from the command line. For each line of the file that contains at least one non-whitespace character, it inserts the prefix followed by a single space at the start of that line. Blank or whitespace-only lines are left exactly as they are.

**Requirements:**

- Use only the Python standard library. Start the file with `from __future__ import annotations`, then import `sys` and `pathlib.Path`.
- Guard all execution logic with `if __name__ == "__main__":` so the module can be imported without side effects.
- **Argument handling:** Expect exactly two positional arguments after the script name: `<filename>` and `<prefix_string>`. If the argument count (`len(sys.argv)`) is not 3, print a usage message to stderr in the form `Usage: <script name> <filename> <prefix_string>` (use `sys.argv[0]` for the script name) and exit with status code 1.
- **File validation:** Wrap the filename in `Path`. If it does not exist or is not a regular file (check with `is_file()`), print an error to stderr such as `Error: <path> does not exist or is not a file` and exit with status 1.
- **Reading:** Read the entire file as text using `read_text()` with default encoding, splitting into lines with `splitlines(keepends=True)` so that original line endings are preserved.
- **Transformation:** Build a new list of lines where each line with non-whitespace content becomes `"<prefix> <original line>"` (prefix, one space, then the line including its newline), and each blank or whitespace-only line is copied unchanged. Use a list comprehension.
- **Writing:** Overwrite the same file with `write_text` using the joined result. No backup file is created, so the operation is destructive and in-place.
- **Output:** On success, print `<path> updated` to stdout.
- **Edge cases to honor:** An empty file produces no output lines and is rewritten as empty. A last line without a trailing newline stays without one. The prefix is inserted verbatim with no escaping, so a prefix containing spaces or special characters is used as-is. Files with non-UTF-8 content may raise a decoding error from `read_text`, which is not specially handled and will surface as an uncaught exception.
- **Style:** Keep the script short, idiomatic, and readable, with minimal comments, matching the concise style of a small utility script.

Deliver the complete script as a single file.
---"""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <filename> <prefix_string>", file=sys.stderr)
        sys.exit(1)
    fn = Path(sys.argv[1])
    str_to_add = sys.argv[2]
    if not fn.is_file():
        print(f"Error: {fn} does not exist or is not a file", file=sys.stderr)
        sys.exit(1)
    lines = fn.read_text().splitlines(keepends=True)
    newlines = [f"{str_to_add} {line}" if line.strip() else line for line in lines]
    fn.write_text("".join(newlines))
    print(f"{fn} updated")
