#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python command-line utility with the following specification:

The utility is a small Termux-friendly command-line tool (intended to run under the Termux shebang path for Android) that deletes a range of lines from a text file in place. It must be written in Python 3, starting with a Termux-style shebang line for the Python interpreter and using postponed annotation evaluation via a `__future__` import. It relies only on the Python standard library: `sys` for reading command-line arguments and `pathlib.Path` for file reading and writing.

Inputs come from positional command-line arguments:
- Argument 1: path to the target file (required).
- Argument 2: the starting line number to delete, 1-based and inclusive (required when any range is given).
- Argument 3 (optional): the ending line number, 1-based and inclusive. If omitted, the deletion runs from the start line through the end of the file.

Behavior to reproduce:
- Read the file as UTF-8 text and split it into lines using line-splitting semantics that drop trailing newline characters.
- Convert the line-number arguments to integers. Compute the kept lines as all lines before the start line, followed by all lines after the end line. Note that the end line is used as a zero-based slice start for the trailing portion, so the implementation must follow this slicing convention exactly as the original does.
- Write the kept lines back to the same file as UTF-8, joining them with newline characters. Do not append a trailing newline; overwrite the file in place with no backup.
- Print a single status line in the form "remained: N lines", where N is the number of lines kept.
- Wrap the logic in a function with no return value, and call it only when the script is executed directly (not when imported).

Edge cases and error handling to reproduce faithfully:
- No input validation or explicit error handling is performed. Missing arguments, non-integer line numbers, or a nonexistent file will raise the default Python exceptions and terminate with a traceback.
- If exactly two arguments are supplied after the script name, the end line defaults to the total line count; if exactly three are supplied, both bounds come from the arguments. Any other argument count is not handled and will cause an error when the line-number variables are referenced.
- Line numbers are not clamped or range-checked; out-of-range or inverted values produce whatever slicing yields.
- Because the output is joined without a trailing newline, a file that originally ended with a newline will lose it after editing.
- The file is read and fully rewritten; there is no atomic write or temporary file.

Usage: run from a shell as `script <file> <from>` to delete from a line to the end of the file, or `script <file> <from> <to>` to delete an inclusive range. Make the script executable and keep the output as the single status line.
---"""

from __future__ import annotations

import sys
from pathlib import Path


def delete_lines_from_file() -> None:
    filename = sys.argv[1]
    path = Path(filename)
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(sys.argv) == 4:
        fromline = int(sys.argv[2])
        toline = int(sys.argv[3])
    if len(sys.argv) == 3:
        fromline = int(sys.argv[2])
        toline = len(lines)
    new_lines = lines[: fromline - 1] + lines[toline:]
    path.write_text("\n".join(new_lines), encoding="utf-8")
    print(f"remained: {len(new_lines)} lines")


if __name__ == "__main__":
    delete_lines_from_file()
