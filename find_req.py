#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python script from scratch that searches installed Python package metadata for packages declaring a given dependency.

Purpose: Scan the site-packages directory of a Python 3.14 installation under the Termux environment on Android, find every installed package whose METADATA file declares a particular dependency in a "Requires-Dist" line, and print the name of each matching package's directory.

Requirements:

- Use Python 3 with `from __future__ import annotations` at the top, and the standard library only (`sys` and `pathlib`).
- Begin the file with a shebang line pointing to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/env python`.
- Define a function `process_file(path, text)` that accepts a filesystem path (convert it to a `Path` object defensively) and a target dependency string. It should:
  - Read the file's full text with `read_text()` and convert it to lowercase.
  - Build the search string by prefixing the target with `"requires-dist: "` (the target is also matched in lowercase form, so the caller should pass the name as-is and the match relies on the lowercased file content; note that the target itself is not lowercased before comparison).
  - If that search string appears anywhere in the content, print the name of the file's parent directory (the package's `.dist-info` directory name) to standard output.
  - Return nothing.
- In the `__main__` block:
  - Set the search root to `/data/data/com.termux/files/home/.local/lib/python3.14/site-packages`.
  - Read the dependency name from the first command-line argument, `sys.argv[1]`.
  - Recursively iterate over all files named exactly `METADATA` under the root using `rglob`, and call `process_file` on each one with the target.

Behavior and edge cases to reproduce faithfully:

- Matching is a plain substring check, not a parsed requirement comparison. A target such as `requests` also matches `requests-toolbelt` or `requests[socks]`, and the target is not lowercased, so a mixed-case argument will never match lowercased file content.
- Output is only the `.dist-info` directory names (e.g., `requests-2.31.0.dist-info`), one per line, in the order `rglob` yields them.
- No argument validation is performed: if no argument is given, `sys.argv[1]` raises an `IndexError` and the script terminates with a traceback. There is no usage message, no `--help`, and no exit-code handling.
- If the root directory does not exist, `rglob` yields nothing and the script exits silently with status 0.
- Files that cannot be read (permission errors, decoding errors from `read_text()` using the default locale encoding) will raise exceptions that propagate uncaught and abort the scan. Do not add try/except blocks unless doing so does not change the output for valid inputs; the original has none.
- Do not print anything else (no headers, counts, or progress messages).
- The script is intended to be run directly as `python <script> <dependency-name>` from a Termux shell.

Keep the implementation minimal, with no classes, no third-party imports, no argument parser, and no additional features beyond what is described.
---"""

from __future__ import annotations

import sys
from pathlib import Path


def process_file(path: Path, text: str) -> None:
    path = Path(path)
    content = path.read_text().lower()
    target1 = "requires-dist: " + text
    if target1 in content:
        print(path.parent.name)


if __name__ == "__main__":
    cwd = Path("/data/data/com.termux/files/home/.local/lib/python3.14/site-packages")
    target = sys.argv[1]
    for path in cwd.rglob("METADATA"):
        process_file(path, target)
