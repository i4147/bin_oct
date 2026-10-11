#!/data/data/com.termux/files/usr/bin/env python
"""Write a single Python 3 script, self-contained, using only the standard library, that recursively cleans terminal escape artifacts from `.log` files under the current working directory, in place. Requirements:

**Purpose:** Strip ANSI/terminal control sequences and stray control characters from log files, leaving readable plain text. Intended to run under Termux on Android (the shebang points to the Termux Python path), but it should work on any POSIX-like system with Python 3.

**Startup and file discovery:**
- Begin the file with a Termux-style shebang line for Python (`/data/data/com.termux/files/usr/bin/env python`) and `from __future__ import annotations` so type hints work on older Python 3 versions.
- Use `re` and `pathlib.Path`. No third-party dependencies.
- Define a constant for the log extension, `.log`.
- Operate on `Path.cwd()` and find every file matching the extension recursively with `rglob`, including files in nested subdirectories.
- If no matching files are found, print a message stating that no `.log` files were found and exit cleanly without error.
- Otherwise, print how many files were found and that cleaning is starting, followed by a blank line.

**Cleaning rules:**
- Keep an ordered module-level list of regex patterns targeting escape artifacts. The patterns must cover: a caret followed by an opening bracket (the literal text form of ESC), bracketed SGR-style color codes containing digits, uppercase letters, and semicolons followed by `m`, bracketed cursor-movement codes with a number and an uppercase letter, general bracketed parameter sequences, literal `^M`, the character-set designators `(B` and `(0`, full ESC CSI sequences (ESC `[`, optional digits and semicolons, then a letter), ESC followed by a character-set designator (`0`, `1`, `2`, `A`, `B`), carriage return characters, and the shift-out and shift-in control characters (0x0E and 0x0F). Use raw strings for the regexes and keep them in this order.
- `clean_line(line)` applies each pattern in order with `re.sub` removing matches, then collapses runs of two or more spaces into a single space. Return the result. Do not strip newlines explicitly beyond what the patterns remove.

**File processing:**
- `clean_file(path)` takes a path and:
  - Reads all lines, opening the file with UTF-8 encoding and `errors="ignore"` so undecodable bytes are dropped silently.
  - Cleans each line with `clean_line`.
  - Reopens the same file in write mode with UTF-8 encoding and writes the cleaned lines back, overwriting the original in place.
  - On success, prints a line starting with a check mark, "Cleaned:", followed by the path.
  - Wrap the whole operation in a try/except catching `Exception`; on failure print a line starting with a cross mark, "Error processing", the path, and the exception message, and continue without raising. Failures on one file must not stop processing of the others.

**Main flow:**
- `main()` returns nothing. Gather the files, handle the empty case as described, otherwise loop over each file calling `clean_file`.
- After processing, print a blank line followed by a completion message stating how many files were processed.
- The entry point is guarded by `if __name__ == "__main__":` and runs `main()` via `raise SystemExit(main())`.

**Behavior notes and edge cases to preserve:**
- Modification is destructive and in place; there is no backup. The script overwrites files without confirmation.
- Files are read fully into memory as a list of lines.
- Encoding errors on read are ignored, so non-UTF-8 bytes are lost on write-back.
- Matches are removed regardless of position in the line; patterns are applied sequentially, so earlier removals can affect later matches.
- Symlinks and permission errors are handled only through the per-file exception catch.
- Output uses Unicode check and cross symbols.

**Output format:** Provide only the complete Python source file as the answer.
---"""

from __future__ import annotations

import re
from pathlib import Path

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
