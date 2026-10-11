#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script that normalizes a text file in place, line by line, with these requirements:

**Purpose:** Read a UTF-8 text file and rewrite it so that each line is converted into a normalized, slug-like form. The file is modified in place.

**Invocation:** The script takes exactly one posit input file. It must be runnable as an executable with a Termux-style shebang line (`#!/data/data/com.termux/files/usr/bin/env python`). Begin the file with `from __future__ import annotations`.

**Argument handling:**
- If the number of command-line arguments (excluding the script name) is not exactly one, print a usage message to stderr in the form `Usage: <script basename> INPUT_FILE` and exit with status 2.
- Convert the argument to a path. If it is not an existing regular file, print `Error: not a file: <path>` to stderr and exit with status 1.

**Per-line normalization (applied to each line in this order):**
1. Apply Unicode NFKC normalization.
2. Remove every character that is not printable (per Python's `str.isprintable`).
3. Remove every character whose Unicode general category begins with `P` (all punctuation).
4. Apply `casefold()`.
5. Split on any whitespace (runs of whitespace collapse) and join the tokens with a single underscore `_`. This also strips leading and trailing whitespace.

**File processing:**
- Read the source file with UTF-8 encoding and `newline=""` so original line endings are preserved for stripping.
- For each line, strip trailing `\\r` and `\\n` characters only, normalize it, and write the result followed by a single `\\n` to a temporary file.
- The temporary file must be created in the same directory as the input file, using UTF-8 encoding, `\\n` newlines, a prefix of `.<original filename>.`, a suffix of `.tmp`, and `delete=False`.
- Once writing is complete, atomically replace the original file with the temporary file (`Path.replace`). Both file handles should be managed via context managers, with the source and temporary file opened in a single combined `with` statement.
- Empty lines produce empty output lines (an empty normalized string followed by `\\n`).

**Error handling:** The call to the file-processing routine in `main` is wrapped in a `try` block. The exception handling should report failures to the user via stderr and exit with a non-zero status rather than printing a traceback. (Ensure any temporary file left behind on failure is not silently relied upon; the replacement only occurs on success.)

**Entry point:** Guard execution with `if __name__ == "__main__":` and call `main()`.

**Dependencies:** Only the Python standard library is used: `sys`, `tempfile`, `unicodedata`, and `pathlib`. No third-party packages.

**Edge cases to honor:**
- Files with CRLF, LF, or mixed line endings all become LF-terminated.
- A file with no trailing newline gains one.
- Non-ASCII text is preserved through NFKC normalization, but punctuation and non-printable characters are dropped.
- Lines consisting only of punctuation or whitespace become empty lines.
- Input files must be UTF-8 decodable; decoding errors should surface through the error handling path.

Provide the complete script as the output of the task.
---"""

from __future__ import annotations

import sys
import tempfile
import unicodedata
from pathlib import Path


def normalize_line(line: str) -> str:
    text = unicodedata.normalize("NFKC", line)
    text = "".join(char for char in text if char.isprintable())
    text = "".join(char for char in text if not unicodedata.category(char).startswith("P"))
    text = text.casefold()
    text = "_".join(text.split())
    return text


def normalize_file_in_place(path: Path) -> None:
    with (
        path.open("r", encoding="utf-8", newline="") as source,
        tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary,
    ):
        temporary_path = Path(temporary.name)
        for line in source:
            content = line.rstrip("\r\n")
            temporary.write(normalize_line(content) + "\n")
    temporary_path.replace(path)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} INPUT_FILE", file=sys.stderr)
        raise SystemExit(2)
    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f"Error: not a file: {input_path}", file=sys.stderr)
        raise SystemExit(1)
    try:
        normalize_file_in_place(input_path)
    except UnicodeDecodeError:
        print(
            f"Error: {input_path} is not valid UTF-8.",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
