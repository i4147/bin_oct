#!/data/data/com.termux/files/usr/bin/env python
"""Write a single, self-contained Python command-line script named clean_text.py that removes invisible and control characters from a text file in place. Requirements:

**Purpose:** Read a UTF-8 text file, strip out all Unicode characters belonging to the "Other" category (control characters, format characters, unassigned, private-use, and surrogate code points, i.e., any character whose Unicode general category begins with "C"), except for newline (\\n), carriage return (\\r), and tab (\\t), which must be preserved. Overwrite the same file with the cleaned content.

**Dependencies:** Use only the Python standard library: `sys`, `unicodedata`, and `pathlib.Path`. Include `from __future__ import annotations` for type hint compatibility. Add a shebang line pointing to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/env python`. Type-annotate all function signatures (the function returns None).

**Structure:**
- A function `clean_file(filename: str) -> None` that performs the work.
- A `__main__` guard that reads the command-line argument.

**Behavior details:**
1. Open the file with UTF-8 encoding and read all lines into a list (preserving line endings).
2. For each line, build a new string by keeping every character `ch` where either its category's first letter is not "C", or `ch` is one of `\\n`, `\\r`, `\\t`. Discard all others. Collect the cleaned lines in a list.
3. Reopen the same file in write mode with UTF-8 encoding and write the cleaned lines back with `writelines`. Note this is an in-place overwrite with no backup.
4. On success, print exactly: `Successfully cleaned: <filename>`.

**Error handling:**
- If the file does not exist (`FileNotFoundError`), print: `Error: The file '<filename>' was not found.`
- For any other exception, print: `An error occurred: <exception message>` (using the exception's string form). Do not re-raise; the script exits normally.
- The usage check: if fewer than two command-line arguments are provided (script name plus filename), print exactly `Usage: python clean_text.py <filename>` and do not attempt any file operation. Only the first filename argument is used; extra arguments are ignored.

**Edge cases to honor:**
- Empty files: produce an empty output with no error.
- Files with Windows (`\\r\\n`) line endings: preserve `\\r` and `\\n`.
- Tabs are preserved; other control characters such as NUL, backspace, escape, zero-width space, BOM (U+FEFF, format character), and soft hyphen are removed.
- Ordinary letters, digits, punctuation, spaces, and non-ASCII printable text (including CJK, accented letters, emoji with category "So") must be kept unchanged.
- Because the file is opened for writing only after reading completes, an error during reading leaves the file untouched.
- Invalid UTF-8 input will raise a decode error caught by the generic exception handler, and the file will not be modified.

**Usage:** Run from the command line as `python clean_text.py <filename>`. The script takes no other options, produces no return value, and writes only status messages to standard output.

**Code style:** Keep it concise, idiomatic, and readable, with a short docstring or comments only where they clarify the character-filtering logic.
---"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path


def clean_file(filename: str) -> None:
    try:
        with Path(filename).open(encoding="utf-8") as f:
            lines = f.readlines()
        cleaned_lines = []
        for line in lines:
            cleaned_line = "".join(ch for ch in line if unicodedata.category(ch)[0] != "C" or ch in "\n\r\t")
            cleaned_lines.append(cleaned_line)
        with Path(filename).open("w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)
        print(f"Successfully cleaned: {filename}")
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_text.py <filename>")
    else:
        target_file = sys.argv[1]
        clean_file(target_file)
