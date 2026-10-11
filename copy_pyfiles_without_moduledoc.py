#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 script (intended for Termux on Android, with a `#!/data/data/com.termux/files/usr/bin/env python` shebang line at the top) that does the following:

**Purpose:** Scan the current working directory for Python files that lack a module docstring and move each of them into a holding folder under the user's home directory, so that un-documented scripts can be collected and reviewed.

**Structure and behavior:**

- Begin the file with the Termux-specific shebang line, then a `from __future__ import annotations` import. Use only the standard library: `shutil` and `pathlib.Path`.
- Define a helper `has_module_docstring(path: Path) -> bool` that:
  - Reads the file as UTF-8 text.
  - If the content starts with `#!` (a shebang), return `False` outright. This is an intentional quirk: any file with a shebang is treated as lacking a docstring, regardless of what follows.
  - Otherwise, strip leading whitespace and return `True` only if the remaining text begins with a triple-double-quote or triple-single-quote string delimiter.
- Define `main() -> None` that:
  - Sets the source directory to the current working directory (`Path()`, i.e. relative `.`).
  - Sets the destination to `~/tmp/notannotated`, creating it and any missing parents with `mkdir(parents=True, exist_ok=True)`.
  - Iterates over `*.py` files in the source directory in reverse-sorted order (`sorted(..., reverse=True)`). Only the top level of the directory is scanned; no recursion.
  - Skips any entry that is not a regular file (e.g., directories whose names end in `.py`).
  - For each file where `has_module_docstring` returns `False`, moves it with `shutil.move` into the destination directory, keeping the same filename, and prints a line of the form `moved: <source> -> <destination>`.
  - Files that already have a docstring are left untouched and produce no output.
- Guard the entry point with `if __name__ == "__main__": main()`.

**Edge cases and notes to preserve:**

- The script does not move itself deliberately, but since it runs from the directory it scans, it will move itself if it lacks a docstring and carries a shebang (in which case it is moved, since shebang files are classified as undocumented). Reproduce this behavior faithfully without adding special-case protection.
- If a destination file with the same name already exists, `shutil.move` behavior applies (it may overwrite or nest depending on the target); do not add custom collision handling.
- Files that cannot be decoded as UTF-8 will raise an exception; no try/except is used, so errors propagate and terminate the script.
- Empty `.py` files are treated as lacking a docstring and will be moved.
- Leading whitespace before a docstring is tolerated for files without a shebang, but a shebang always causes the file to be classified as undocumented.
- No command-line arguments are accepted; no logging framework is used; output is only the `print` lines.

**Usage:** Run the script from the directory containing the Python files to triage, e.g. `python3 script.py` in Termux. Return only the complete script.
---"""

from __future__ import annotations

import shutil
from pathlib import Path


def has_module_docstring(path: Path) -> bool:
    code = path.read_text(encoding="utf-8")
    if not code.startswith("#!"):
        s = code.lstrip()
        return s.startswith(('"""', "'''"))
    else:
        return False


def main() -> None:
    source_dir = Path()
    dest_dir = Path.home() / "tmp" / "notannotated"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for py_file in sorted(source_dir.glob("*.py"), reverse=True):
        if not py_file.is_file():
            continue
        if not has_module_docstring(py_file):
            dest = dest_dir / py_file.name
            shutil.move(py_file, dest)
            print(f"moved: {py_file} -> {dest}")


if __name__ == "__main__":
    main()
