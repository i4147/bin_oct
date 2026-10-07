#!/data/data/com.termux/files/usr/bin/env python
"""Copy .py files without module docstrings to ~/tmp/notannotated."""

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
