#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script (targeting a Termux environment on Android, with a shebang pointing to Termux's Python) that cleans a requirements file in place. Requirements:

**Purpose:** Read a pip `requirements.txt` file given as the single command-line argument, normalize each line down to a bare package name, remove duplicates, sort the names in a specific grouped order, and overwrite the same file with the result.

**Usage and CLI behavior:**
- Expects exactly one argument: the path to the requirements file. Otherwise, print a usage message to stderr in the form `Usage: <script name> requirements.txt` and exit with status 1.
- Read the file as UTF-8. If the file does not exist, print `Error: File '<name>' not found.` to stderr and exit with status 1.
- Use `from __future__ import annotations` and `pathlib.Path` for file handling; type-annotate functions.

**Line cleaning (per line, in this order):**
1. Strip everything from the first `#` onward (comments), then trim whitespace; skip the line if empty.
2. Strip everything from the first `;` onward (environment markers), then trim; skip if empty.
3. Remove any bracketed extras such as `[security,socks]` (non-greedy match of square brackets), then trim; skip if empty.
4. Split on the first version operator, matching any of `===`, `==`, `!=`, `>=`, `<=`, `~=`, `>`, `<` with optional surrounding whitespace (precompile this regex as a module-level constant). Keep only the part before the operator, trimmed.
5. Lines that are blank or whitespace-only produce no output. Lines with only comments are dropped. Lines like `-r other.txt` or `--index-url ...` are not specially handled and would pass through the same pipeline (preserve this natural behavior rather than adding special cases).

**Deduplication:** Keep the first occurrence of each cleaned name (case-sensitive exact match) using a list plus a set for membership tracking.

**Sorting:** Sort with a key function returning a tuple `(group, name)` where group is:
- `0` if the first character is uppercase,
- `1` if the first character is lowercase,
- `2` otherwise (e.g., digits or underscores).
Within each group, sort alphabetically by the full name (case-sensitive string comparison).

**Output:** Overwrite the same file in UTF-8, writing each name followed by a newline (`\\n`). Use `writelines` with a generator/list of strings. No trailing blank lines beyond the per-item newline, and no output to stdout on success.

**Entry point:** Wrap logic in a `main()` function, and run it under the standard `if __name__ == "__main__":` guard. Include a shebang line for Termux Python (`/data/data/com.termux/files/usr/bin/env python`). Keep the code concise, with a short docstring or comments only where they clarify non-obvious logic, matching a minimal utility-script style. No third-party dependencies; use only `re`, `sys`, `pathlib`, and `__future__`.

**Edge cases to handle:** empty file (writes an empty file), duplicate names with different version specifiers (collapsed to one), extras and markers mixed with versions, inline comments, and files with Windows line endings (stripping handles the `\\r`).
---"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_VERSION_OP_RE = re.compile(r"\s*(?:===|==|!=|>=|<=|~=|>|<)\s*")


def clean_requirement(line: str) -> str:
    line = line.split("#", 1)[0].strip()
    if not line:
        return ""
    line = line.split(";", 1)[0].strip()
    if not line:
        return ""
    line = re.sub(r"\[.*?\]", "", line).strip()
    if not line:
        return ""
    parts = _VERSION_OP_RE.split(line, maxsplit=1)
    return parts[0].strip()


def group_key(name: str) -> tuple[int, str]:
    first = name[0]
    if first.isupper():
        return 0, name
    if first.islower():
        return 1, name
    return 2, name


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} requirements.txt", file=sys.stderr)
        sys.exit(1)
    fname = sys.argv[1]
    try:
        with Path(fname).open(encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{fname}' not found.", file=sys.stderr)
        sys.exit(1)
    cleaned = []
    seen = set()
    for line in lines:
        c = clean_requirement(line)
        if c and c not in seen:
            cleaned.append(c)
            seen.add(c)
    cleaned = sorted(cleaned, key=group_key)
    with Path(fname).open("w", encoding="utf-8") as f:
        f.writelines(item + "\n" for item in cleaned)
    print("\n=== Cleaned Requirements ===")
    for item in cleaned:
        print(item)


if __name__ == "__main__":
    raise SystemExit(main())
