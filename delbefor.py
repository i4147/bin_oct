#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script (intended to run under Termux on Android, so include the Termux-style shebang `#!/data/data/com.termux/files/usr/bin/env python`) that edits a text file in place. Requirements:

**Purpose:** For each line of a given text file, strip leading and trailing whitespace. If the line is non-empty and contains a specified target substring, remove everything before the first occurrence of that substring (keeping the target substring and everything after it). If the line is non-empty but does not contain the target substring, keep the stripped line unchanged. Empty lines (after stripping) are dropped entirely. Finally, overwrite the original file with the resulting lines joined by newline characters, encoded as UTF-8.

**Inputs:**
- `sys.argv[1]`: path to the target text file (converted to a path object).
- `sys.argv[2]`: the target substring to search for in each line (taken verbatim as a string; matching is case-sensitive and uses plain substring search, not regex).

**Outputs:**
- No printed output. The file at `sys.argv[1]` is rewritten in place. If no non-empty lines result, the file is left unchanged (not truncated or rewritten).

**Dependencies:**
- Standard library: `sys`, `pathlib.Path`, and `from __future__ import annotations`.
- A helper module named `dh` that provides a function `read_lines(path)` which yields or returns the lines of the file. Import it as `from dh import read_lines`. Do not reimplement it; assume it exists.

**Key logic and structure:**
- Define a module-level constant `THRESHOLD = 1048576` (1 MiB). It is defined but not used anywhere in the logic; reproduce it as-is.
- Wrap all execution under `if __name__ == "__main__":`.
- Read arguments, initialize an empty accumulator list, and iterate over `read_lines(file_name)`.
- For each line: compute `stripped = line.strip()`. Then branch:
  - If `stripped` is truthy and `target_char in stripped`: find the index of the first occurrence with `stripped.index(target_char)`, slice from that index to the end, and append the slice.
  - Else if `stripped` is truthy: append `stripped`.
  - Otherwise (empty line): skip.
- After the loop, if the accumulator is non-empty, write `"\\n".join(accumulator)` to the file with UTF-8 encoding using `Path.write_text`.
- No trailing newline is added to the written content.

**Error handling and edge cases:**
- There is no explicit error handling: missing arguments (fewer than two) cause an `IndexError`; a nonexistent input file causes whatever `read_lines` raises; no try/except blocks are used.
- An empty target string `""` would match every non-empty line at index 0, so lines remain unchanged apart from stripping.
- Whitespace-only lines are treated as empty and removed.
- The target substring is matched after stripping, so leading whitespace before the target is removed as part of the stripping step, and the kept portion begins exactly at the first match.
- Only the first occurrence of the target is used for trimming; later occurrences are retained.
- If every line is empty, the file is not modified at all.
- Encoding on read is delegated to `read_lines`; writing is always UTF-8.

**Execution and usage:**
- Run from the command line as: `python <script> <file_path> <target_substring>`.
- Intended to be executed directly as an executable script with the Termux Python shebang, so the script should be marked executable when deployed.
- Only the minimal necessary code should be produced: no extra functions, classes, argument parsing libraries, logging, or user-facing messages beyond what is described above.
---"""

from __future__ import annotations

import sys
from pathlib import Path

from dh import read_lines

THRESHOLD = 1048576
if __name__ == "__main__":
    file_name = Path(sys.argv[1])
    nl = []
    target_char = sys.argv[2]
    for line in read_lines(file_name):
        stripped = line.strip()
        if stripped and target_char in stripped:
            indx = stripped.index(target_char)
            cleaned = stripped[indx:]
            nl.append(cleaned)
        elif stripped:
            nl.append(stripped)
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")
