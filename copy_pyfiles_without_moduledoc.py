#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory for Python source files and relocates those that lack a module-level docstring into a dedicated folder under the user's home directory, creating that folder if it does not already exist.
The script should process only regular files with a ".py" extension located directly in the current directory (not in subdirectories), and handle them in reverse alphabetical order. For each file, determine whether it begins with a module docstring, using these rules: a leading shebang line ("#!") means the file is treated as not having a docstring; otherwise, ignoring leading whitespace, the file is considered to have a docstring if its content starts with a triple-quoted string (either triple double quotes or triple single quotes). Read files as UTF-8 text.
Files that do not have a module docstring should be moved (not copied) into the destination folder, keeping their original filenames. Files that already have a docstring must be left untouched in place. After each successful move, print a single-line message in the format "moved: <original path> -> <destination path>" so the user can see what was relocated.
The script should run its main logic only when executed directly, not when imported as a module. Keep the implementation simple, dependency-free (standard library only), and robust for typical use: it should not crash on the destination folder already existing, and it should follow the behavior above without requiring any command-line arguments.
---"""

from __future__ import annotations
from pathlib import Path
import shutil


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
