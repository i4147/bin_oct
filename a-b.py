#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script that removes from one text file every line that also appears in a second text file, and rewrites the first file in place.

Requirements:

**Interface**
- Run as a command-line program that takes exactly two positional arguments: the path to the file to be edited (call it file A) and the path to the file whose lines serve as the removal list (call it file B).
- Begin with a Termux-style shebang pointing to `/data/data/com.termux/files/usr/bin/env python`.
- Include `from __future__ import annotations` at the top.
- Use `sys` for argument access and `pathlib.Path` for all file handling.
- Define a `main()` function returning `None`, and run it under an `if __name__ == "__main__":` guard using `raise SystemExit(main())`.

**Behavior**
1. Read file B as UTF-8 text and build a set of its lines, with each line's trailing newline stripped. Use line splitting that does not keep line endings, so Windows and Unix line endings are both handled.
2. Read file A as UTF-8 text, preserving line endings (keep the newline characters with each line).
3. Keep only those lines of file A whose content, with a trailing newline stripped, does not appear in file B's set. Lines are compared exactly otherwise; no trimming of spaces, no case folding, and no normalization of duplicates. Every duplicate of a matching line in file A is removed, and non-matching lines keep their original order and original line endings.
4. Write the kept lines to a temporary file placed next to file A, named by appending `.tmp` to file A's full name (for example, if file A is `notes.txt`, the temp file is `notes.txt.tmp`). Write it as UTF-8 with no added line endings beyond those preserved.
5. Atomically replace file A with the temporary file using `Path.replace`, so the original is overwritten only after the new content is fully written.

**Edge cases and error handling**
- If file A is empty, the result is an empty file (still rewritten through the temp file).
- If every line of file A matches file B, file A ends up empty.
- If file B is empty, no lines are removed, but file A is still rewritten through the temp-file process.
- A final line in file A without a trailing newline is preserved as-is when kept; a matching final line without a newline is still matched correctly.
- Do not add explicit try/except blocks; let missing-file, permission, or decoding errors propagate naturally as exceptions.
- Do not print any output on success and do not return a meaningful exit code; `main()` returns `None`, so the process exits with status 0 on success.

**Dependencies**
- Python standard library only: `sys`, `pathlib`, and `__future__`. No third-party packages.

**Usage**
- Invoked as `python script.py FILE_A FILE_B`, with the file to modify given first.
- Warn in the docstring or comments that file A is modified in place and is not backed up.

Output only the complete script.
---"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    file_a = Path(sys.argv[1])
    file_b = Path(sys.argv[2])
    b_lines = {line.rstrip("\n") for line in file_b.read_text(encoding="utf-8").splitlines()}
    a_lines = file_a.read_text(encoding="utf-8").splitlines(keepends=True)
    kept_lines = [line for line in a_lines if line.rstrip("\n") not in b_lines]
    tmp_path = file_a.with_suffix(file_a.suffix + ".tmp")
    tmp_path.write_text("".join(kept_lines), encoding="utf-8")
    tmp_path.replace(file_a)


if __name__ == "__main__":
    raise SystemExit(main())
