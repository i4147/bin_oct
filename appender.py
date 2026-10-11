#!/data/data/com.termux/files/usr/bin/env python
"""Write a single self-contained Python 3 script that appends the contents of a shared prompt file to every `.txt` file in the current working directory. Requirements:

**Purpose:** Batch-append a common text block to all text files in the current directory, intended for a Termux (Android) environment where the script is run with the Termux Python shebang.

**Dependencies:** Only the Python standard library. Use `from __future__ import annotations` at the top and `pathlib.Path` for all file handling. No third-party packages.

**Inputs:**
- A source file named `prompt.txt` located in the user's home directory (resolved via `Path.home()`), read as UTF-8.
- Target files: every file in the current working directory (`Path.cwd()`) whose name matches the glob `*.txt`. Only the top level of the current directory is scanned; do not recurse into subdirectories.

**Outputs:**
- Side effect: each matching target file has the full contents of `prompt.txt` appended to the end of its existing contents, with no separator inserted (the content is concatenated directly). Files are read as UTF-8 and rewritten as UTF-8.
- Console output: one line per target file. On success, print `✓ Updated: <filename>` (filename only, not the full path). On failure, print `✗ Error: <filename> - <exception message>`.

**Key logic and structure:**
- Place all top-level execution under an `if __name__ == "__main__":` guard.
- Read `prompt.txt` once before iterating over targets.
- Iterate over `Path.cwd().glob("*.txt")`.
- For each file, read its current text, concatenate the prompt text after it, and write the combined text back to the same path, all within a `try` block so that one file's failure does not stop processing of the others.
- Catch `Exception` broadly and report the error message via the `✗` line.

**Error handling and edge cases:**
- If `prompt.txt` does not exist or is unreadable in the home directory, let the resulting exception surface (the script does not need to catch it); it occurs before any target is modified, so no partial changes are made.
- If no `.txt` files exist in the current directory, the script completes silently with no output.
- The `prompt.txt` file itself is a `.txt` file in the home directory, not the current directory, so it is only excluded when the user runs the script from their home directory; be aware that running from `~` would also append `prompt.txt` to itself (duplicating its content). Reproduce the behavior as written without adding extra guards unless noted.
- Files are overwritten in place; there is no backup, no dry-run mode, and no confirmation prompt.
- Non-`.txt` files, hidden files without the `.txt` suffix, and subdirectories are ignored.
- Encoding is always UTF-8; non-UTF-8 target files will produce an error line for that file only.

**Execution details:**
- The script begins with a Termux-specific shebang line: `#!/data/data/com.termux/files/usr/bin/env python`.
- Intended to be run from the directory containing the target `.txt` files, e.g. `cd` into that directory and execute the script.
- Output uses the Unicode check mark (✓) and cross mark (✗) characters.
- Keep the script short and minimal, with no argument parsing, logging module, or configuration files.
---"""

from __future__ import annotations

from pathlib import Path

if __name__ == "__main__":
    fn = Path.home() / "prompt.txt"
    text = fn.read_text(encoding="utf-8")
    for py_file in Path.cwd().glob("*.txt"):
        try:
            py_file.write_text(py_file.read_text(encoding="utf-8") + text, encoding="utf-8")
            print(f"✓ Updated: {py_file.name}")
        except Exception as e:
            print(f"✗ Error: {py_file.name} - {e}")
