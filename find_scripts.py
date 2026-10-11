#!/data/data/com.termux/files/usr/bin/env python
"""Build a self-contained Python command-line script that finds Python scripts lacking a file extension in the current directory tree. Requirements:

**Purpose:** Recursively scan the current working directory (including subdirectories) and report every regular file that has no suffix, is not binary, begins with a shebang line (`#!`), and is recognized as a Python file by a helper check.

**Target environment:** Termux on Android. The script's shebang line should be `#!/data/data/com.termux/files/usr/bin/env python`. Use `from __future__ import annotations` and `pathlib.Path`.

**Dependencies:** The script imports four helper functions from a local module named `dh`: `get_filez`, `is_binary`, `is_python_file`, and `should_skip`. Do not reimplement them; assume they exist in that module and import them directly. `get_filez(directory)` yields file/path items under a directory (recursively), `should_skip(item)` returns True for paths to ignore, `is_binary(item)` returns True for binary files, and `is_python_file(item)` returns True when the file is a Python script.

**Structure:**

1. A function `has_shebang(path)` that opens the file in binary mode, reads the first two bytes, and returns True only if they equal `#!`. It must not read more than needed.

2. A function `find_scripts_without_extension(directory: Path)` that:
   - Iterates over `get_filez(directory)`.
   - Skips any item for which `should_skip` returns True.
   - Keeps only items that are files (`is_file()`) with an empty `suffix`.
   - Skips binary files via `is_binary`.
   - Appends items where `has_shebang` and `is_python_file` both return True.
   - Returns the list of matching `Path` objects.

3. A `__main__` block that:
   - Gets the current directory with `Path.cwd()`.
   - Calls the finder on it.
   - If results exist, prints the header `Found Python scripts without extension (relative paths):` followed by each script's path relative to the current directory (via `relative_to(cwd)`), one per line.
   - Otherwise prints `No Python scripts without extension found in the current directory or its subdirectories.`

**Behavior and edge cases:**
- Output uses relative paths only.
- Files that are binary, have an extension (including hidden dotfiles treated per `Path.suffix` semantics), are directories, or lack a shebang are excluded.
- Files that are skipped by `should_skip` are never inspected.
- The shebang check reads only two bytes, so it is safe for large files; a file shorter than two bytes simply fails the check.
- No explicit exception handling is required beyond what the helpers provide; unreadable files would raise normally from the helper calls.
- Execution: run directly from the directory to scan (`python <scriptname>`); no command-line arguments are accepted, and the scan root is always the current working directory.
- Keep the code minimal, with no extra features, no output formatting beyond the specified messages, and no additional imports beyond those listed.
---"""

from __future__ import annotations

from pathlib import Path

from dh import get_filez, is_binary, is_python_file, should_skip


def has_shebang(path):
    with path.open("rb") as f:
        first_two = f.read(2)
        if first_two == b"#!":
            return True
    return False


def find_scripts_without_extension(directory: Path):
    swe = []
    for item in get_filez(directory):
        if should_skip(item):
            continue
        if item.is_file() and (not item.suffix):
            if is_binary(item):
                continue
            if has_shebang(item) and is_python_file(item):
                swe.append(item)
    return swe


if __name__ == "__main__":
    cwd = Path.cwd()
    found_scripts = find_scripts_without_extension(cwd)
    if found_scripts:
        print("Found Python scripts without extension (relative paths):")
        for script_path in found_scripts:
            print(script_path.relative_to(cwd))
    else:
        print("No Python scripts without extension found in the current directory or its subdirectories.")
