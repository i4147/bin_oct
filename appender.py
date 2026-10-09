#!/data/data/com.termux/files/usr/bin/env python

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
