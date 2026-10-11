#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script that compares two text files line by line and prints a summary report. Requirements:

**Purpose and behavior:**
- Accept exactly two positional command-line arguments: the paths to two text files (file1 and file2). If the argument count is not exactly two, print a usage message in the form `Usage: python <script_name> <file1> <file2>` and exit.
- Open both files for reading using UTF-8 encoding, via `pathlib.Path`, inside a single combined `with` statement (parenthesized context managers, Python 3.10+ syntax is acceptable).
- Read all lines from each file, then strip only the trailing newline character from each line (use `rstrip("\\n")`, not full whitespace stripping), so leading and trailing spaces and carriage returns other than `\\n` are preserved.
- If either file is missing (`FileNotFoundError`), print `Error: <exception message>` and return without further output. Do not catch other exception types.

**Comparison logic (membership-based, not positional):**
- A line from file1 is considered "different" if its exact string does not appear anywhere in file2's line list. Record its 1-based line number.
- A line from file2 is considered "different" if its exact string does not appear anywhere in file1's line list. Record its 1-based line number.
- Compute `common_count` as the number of lines in file1 whose exact string appears in file2 (counted per occurrence in file1, including duplicates).
- Membership checks use simple list `in` tests; duplicates are not deduplicated and order is not considered.

**Output format (print exactly these lines, in this order):**
1. `<file1 path as given> : <number of lines in file1>`
2. `<file2 path as given> : <number of lines in file2>`
3. `common: <common_count>`
4. `Number of different lines in File 1: <count>`
5. If that count is greater than zero, `Line numbers: [<list of 1-based line numbers>]` (Python list repr format)
6. `Number of different lines in File 2: <count>`
7. If that count is greater than zero, `Line numbers: [<list of 1-based line numbers>]`

**Script structure and conventions:**
- Start with a Termux-style shebang line: `#!/data/data/com.termux/files/usr/bin/env python`.
- Begin the file with `from __future__ import annotations`.
- Use `sys` for argv and `pathlib.Path` for file access; no third-party dependencies, standard library only.
- Define a function `compare_files(file1: str, file2: str) -> None` with type hints containing the logic above.
- Guard the entry point with `if __name__ == "__main__":`, perform the argument-count check there, and call `compare_files(sys.argv[1], sys.argv[2])`.
- Use f-strings for all output formatting.

**Edge cases to handle naturally by the logic described:**
- Empty files (zero lines) produce count 0 and no line-number lists.
- Files with identical content produce zero different lines on both sides.
- Duplicate lines are each counted and checked independently.
- Files with a final line lacking a trailing newline are handled the same as others.
- Non-UTF-8 content will raise a decoding error that is not caught (propagates as an uncaught exception).

**Execution:** Run from the command line as `python <script_name> <file1> <file2>`, e.g., on Termux or any Python 3.10+ environment.
---"""

from __future__ import annotations

import sys
from pathlib import Path


def compare_files(file1: str, file2: str) -> None:
    try:
        with (
            Path(file1).open("r", encoding="utf-8") as f1,
            Path(file2).open("r", encoding="utf-8") as f2,
        ):
            lines1 = f1.readlines()
            lines2 = f2.readlines()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    lines1 = [line.rstrip("\n") for line in lines1]
    lines2 = [line.rstrip("\n") for line in lines2]
    diff_lines_1 = []
    diff_lines_2 = []
    common_count = 0
    for i, line in enumerate(lines1):
        if line not in lines2:
            diff_lines_1.append(i + 1)
    for i, line in enumerate(lines2):
        if line not in lines1:
            diff_lines_2.append(i + 1)
    for line in lines1:
        if line in lines2:
            common_count += 1
    print(f"{file1} : {len(lines1)}")
    print(f"{file2} : {len(lines2)}")
    print(f"common: {common_count}")
    print(f"Number of different lines in File 1: {len(diff_lines_1)}")
    if diff_lines_1:
        print(f"Line numbers: {diff_lines_1}")
    print(f"Number of different lines in File 2: {len(diff_lines_2)}")
    if diff_lines_2:
        print(f"Line numbers: {diff_lines_2}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <file1> <file2>")
        sys.exit(1)
    compare_files(sys.argv[1], sys.argv[2])
