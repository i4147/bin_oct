#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with the following specification:

Create a single-file Python 3 command-line script, intended to run under Termux on Android (use the shebang `#!/data/data/com.termux/files/usr/bin/env python`). Begin the file with `from __future__ import annotations`. Use only the standard library: `zipfile` and `pathlib`. Do not add any third-party dependencies.

**Purpose:** The script scans the current working directory recursively for Python wheel files (`*.whl`) and moves any "empty" wheels into a subfolder named `empty_wheels`. A wheel is considered empty if it contains no files whose names end in `.py`, `.so`, or `.pyi` (match case-insensitively). Wheels containing any such file are left untouched.

**Required components:**

1. A helper function `is_empty_wheel(whl_path: Path) -> bool | None` that:
   - Opens the file as a ZIP archive in read mode using `zipfile.ZipFile`.
   - Iterates over all member names; if any name, lowercased, ends with one of `.py`, `.so`, or `.pyi`, it returns `False` immediately.
   - If the archive is fully scanned with no matching names, it returns `True`.
   - If the file raises `zipfile.BadZipFile`, it prints a warning in the form `Warning: <path> is not a valid ZIP file. Skipping.` and returns `False` (so corrupt files are never moved).
   - Other exceptions (such as missing files or permission errors) are not caught and should propagate.

2. A `main()` function (returning `None`) that:
   - Collects results in a list named `empty_wheels`.
   - Sets `cwd` to the current working directory via `Path.cwd()` and `target` to `cwd / "empty_wheels"`.
   - Iterates over `cwd.rglob("*.whl")`, and for each entry that is a file (`is_file()`), calls `is_empty_wheel` and appends it to the list when the result is truthy. Note that the `target` directory itself is scanned by `rglob`, so already-moved wheels inside it will be found on subsequent runs.
   - If any empty wheels were found: print a blank line followed by `Found N empty wheel(s).` where N is the count. Create the `target` directory with `mkdir(exist_ok=True)` (parent directories are not required to be created separately since `cwd` exists). Then for each wheel, print its path relative to `cwd` (using `relative_to(cwd)`), compute `new_path = target / <filename>`, and move the file with `Path.rename`. Note that `rename` will overwrite an existing file of the same name on POSIX systems and may fail across filesystems; the script does not handle these cases explicitly.
   - If none were found, print `No empty wheels found.`

3. An entry point guarded by `if __name__ == "__main__":` that calls `main()` and exits with `raise SystemExit(main())`. Since `main` returns `None`, this exits with status 0.

**Behavior and edge cases to reproduce:**
- Empty wheels are only identified by file extensions inside the archive, not by size or metadata.
- Recursive search: nested wheels in subdirectories are included, and the printed paths show their relative location, but all moved wheels land directly in `empty_wheels/` (flattened by filename).
- Only files are considered; directories named `*.whl` are skipped.
- Corrupt ZIP files produce a warning and are left in place.
- No progress bars, logging framework, command-line arguments, or configuration. Output is plain `print` statements only.
- No type-checking, confirmation prompts, or dry-run mode.

**Deliverable:** Output the complete script as a single file, following the structure above with type hints and concise, idiomatic style matching the original's naming and comment-free layout.
---"""

from __future__ import annotations

import zipfile
from pathlib import Path


def is_empty_wheel(whl_path: Path) -> bool | None:
    try:
        with zipfile.ZipFile(whl_path, "r") as zf:
            for name in zf.namelist():
                if name.lower().endswith((".py", ".so", ".pyi")):
                    return False
    except zipfile.BadZipFile:
        print(f"Warning: {whl_path} is not a valid ZIP file. Skipping.")
        return False
    return True


def main() -> None:
    empty_wheels = []
    cwd = Path.cwd()
    target = cwd / "empty_wheels"
    for whl in cwd.rglob("*.whl"):
        if whl.is_file():
            is_empty = is_empty_wheel(whl)
            if is_empty:
                empty_wheels.append(whl)
    if empty_wheels:
        print(f"\nFound {len(empty_wheels)} empty wheel(s).")
        target.mkdir(exist_ok=True)
        for k in empty_wheels:
            print(k.relative_to(cwd))
            new_path = target / k.name
            k.rename(new_path)
    else:
        print("No empty wheels found.")


if __name__ == "__main__":
    raise SystemExit(main())
