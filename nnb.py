#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script (targeting a Termux environment on Android, so include the Termux shebang line `#!/data/data/com.termux/files/usr/bin/env python`) that performs the following:

**Purpose:** Convert a text file in place so that every real newline character is replaced by the two-character literal sequence backslash followed by the letter n. The file is rewritten as a single line with no actual line breaks.

**Input:** Exactly one command-line argument, the path to a text file. No other options or flags.

**Output:** The file at that path is overwritten with the transformed content. Nothing is printed on success, and the script produces no separate output file.

**Requirements and behavior:**
- Use `from __future__ import annotations` at the top, followed by `import sys` and `from pathlib import Path`.
- Define a `main()` function returning `None`. Inside it, check that `sys.argv` has exactly two entries (script name plus one filename). If not, print a usage message in the form `Usage: <script name> <filename>` using `sys.argv[0]` for the script name, then exit with status code 1 via `sys.exit(1)`.
- Read the file with `Path(...).read_text(encoding="utf-8")`.
- Replace every `"\\n"` newline character with the two-character string `"\\\\n"` (backslash, n).
- Write the result back to the same path with `Path(...).write_text(content, encoding="utf-8")`.
- Guard the entry point with `if __name__ == "__main__":` and call `raise SystemExit(main())`.

**Edge cases and notes to handle or preserve:**
- The script does not handle carriage returns (`\\r`) separately; on Windows-style line endings, `\\r` remains in the output, and `read_text` applies universal newline translation, so `\\r\\n` is normalized to `\\n` on read before replacement.
- A missing file or unreadable/unwritable path will raise the standard Python exception (e.g., `FileNotFoundError`, `PermissionError`, `UnicodeDecodeError` for non-UTF-8 input) and the script does not catch these; the traceback propagates.
- An empty file is rewritten as empty.
- The file is modified in place with no backup created, so the operation is destructive and not reversible.
- Running with zero or more than one argument triggers the usage message and exit code 1.

**Execution:** Intended to be run as `python <script> <filename>` or directly as an executable script on Termux. Use only the Python standard library; no third-party dependencies.
---"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <filename>")
        sys.exit(1)
    fname = sys.argv[1]
    content = Path(fname).read_text(encoding="utf-8")
    content = content.replace("\n", "\\n")
    Path(fname).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
