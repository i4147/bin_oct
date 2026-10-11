#!/data/data/com.termux/files/usr/bin/python
"""Write a single self-contained Python 3 script (Termux-compatible, with a `#!/data/data/com.termux/files/usr/bin/python` shebang line and `from __future__ import annotations` at the top) that does the following. Describe it precisely enough that another agent can reproduce its behavior exactly, but do not include code or snippets in your own output; write the script from these requirements.

**Purpose:** A command-line text filter that rewrites a file in place, keeping only the portion of each line that lies before or after the first occurrence of a given character, and dropping lines that end up empty.

**Command-line interface:**
- Three positional arguments are read from the system argument list in this order: a mode flag, a file path, and a target character.
- Mode `-a` keeps the text before the first occurrence of the target character on each line.
- Any other mode value (including `-b` or anything else) keeps the text after the first occurrence of the target character.
- No argument parsing library is used; missing or extra arguments are not explicitly validated, so a missing argument should be allowed to raise the natural index error.

**Input and output:**
- The file is read as UTF-8 text, preserving line structure (line endings are kept during reading).
- Each line is processed independently: first strip leading and trailing whitespace from the line.
- If the stripped line is non-empty and contains the target character:
  - Mode `-a`: result is the substring before the first occurrence of the target character (this may be empty, e.g. when the character is at position zero, and that empty result is then dropped).
  - Other modes: result is the substring after the first occurrence of the target character, which is not stripped further (may contain leading spaces; may be empty).
- If the stripped line is non-empty but does not contain the target character, the result is the full stripped line.
- If the stripped line is empty, the result is an empty string.
- Only non-empty results are collected, in order.
- If at least one result was collected, the original file is overwritten in place with the collected results joined by a newline character, with no trailing newline, encoded as UTF-8. If nothing was collected, the file is left unchanged (not truncated).

**Structure:**
- A helper that reads a file path into a list of lines with line endings retained.
- Two helper functions, one for each mode's logic, each taking a line and a target character and returning the processed string as described above. They share the same structure and differ only in the slice taken from the match point.
- A `__main__` guard containing the argument reading, the per-line loop choosing the helper by mode, collection, and the conditional write.
- Type hints using the built-in list generic syntax under the future annotations import.

**Dependencies:** Only the Python standard library (`sys` and `pathlib`).

**Edge cases to reproduce:**
- Blank or whitespace-only lines are removed from the output.
- Lines without the target character are kept (trimmed) in both modes.
- Only the first occurrence of the target character splits a line.
- The target character is matched as a substring test, so a multi-character argument also works by the same logic, with the index taken at its first occurrence.
- The file is always read in full before any writing occurs.
- Files that are missing or undecodable as UTF-8 will raise the standard exceptions without custom handling.

**Usage:** Run directly as an executable script, e.g. `script -a file.txt :` to keep text before colons, or `script -b file.txt :` to keep text after colons. The file is modified in place with no backup, and output is not printed to stdout.
---"""

from __future__ import annotations

import sys
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def process_a(line: str, target_char: str) -> str:
    stripped = line.strip()
    if stripped and target_char in stripped:
        indx = stripped.index(target_char)
        return stripped[:indx]
    elif stripped:
        return stripped
    return ""


def process_b(line: str, target_char: str) -> str:
    stripped = line.strip()
    if stripped and target_char in stripped:
        indx = stripped.index(target_char)
        return stripped[indx + 1 :]
    elif stripped:
        return stripped
    return ""


if __name__ == "__main__":
    mode = sys.argv[1]
    file_name = Path(sys.argv[2])
    target_char = sys.argv[3]
    nl: list[str] = []
    for line in read_lines(file_name):
        if mode == "-a":
            result = process_a(line, target_char)
        else:
            result = process_b(line, target_char)
        if result:
            nl.append(result)
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")
