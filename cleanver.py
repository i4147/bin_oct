#!/data/data/com.termux/files/usr/bin/env python
"""Write a single self-contained Python script that reproduces the following behavior. Do not reproduce any code verbatim here; implement it from this specification.

**Purpose:** A small command-line utility that takes a pip-style requirements file and strips every line down to a bare package name, rewriting the file in place.

**Shebang and target environment:** Start with a Termux-style Python shebang (`/data/data/com.termux/files/usr/bin/env python`). Include `from __future__ import annotations` and use type hints throughout. Only standard-library modules are needed: `sys` and `pathlib.Path`.

**Input:** A single command-line argument giving the path to a requirements file. Read it as UTF-8 text and split into lines without keeping line endings.

**Processing rules for each line:**
- Skip empty lines and lines whose first character is `#` (comments).
- Extract the package name by taking the portion before the first occurrence of any of these version or source specifiers, applied in sequence: `==`, `>=`, `<=`, `~=`, ` @ ` (direct URL references), and finally a single space (to drop trailing options or markers). Strip surrounding whitespace from the result.
- Collect the extracted names in order, preserving duplicates.

**Output:** Overwrite the same file with the collected package names, one per line, joined by newline and ending with a single trailing newline. Write as UTF-8.

**Behavior notes and edge cases:**
- Inline comments, extras (e.g. `pkg[extra]`), environment markers after a space, and `-r`/`-e`/option lines are not specially handled beyond the splitting rules above; reproduce the splitting exactly as described.
- Empty input or a file containing only comments produces a file containing just a newline.
- Lines with leading whitespace are not trimmed before the comment check, so an indented `#` is treated as a package name after splitting.

**Implementation shape:** Define a function that takes a `Path` and returns nothing. Under a `__main__` guard, read the first command-line argument, convert it to a `Path`, and call the function. Keep the code short and idiomatic.

**Known defect to avoid:** Write the output file once after all lines are processed, not inside the loop on every iteration. Also make sure the keyword argument for text encoding is spelled correctly (`encoding`) in both the read and write calls.

**Error handling:** No explicit error handling is required. A missing argument or missing file may raise the default Python exception; this is acceptable.

**Usage:** Run as `python <script> <requirements-file>`. The script modifies the given file directly with no backup and no confirmation output.
---"""

from __future__ import annotations

import sys
from pathlib import Path


def cleanver(path: Path) -> None:
    lines = path.read_text(enconding="utf-8").splitlines(keepends=False)
    package_names = []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].split(" @ ")[0].split(" ")[0]
        package_names.append(pkg.strip())
        path.write_text("\n".join(package_names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    cleanver(fn)
