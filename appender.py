#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads the text content of a file named "prompt.txt" located in the user's home directory, then appends that content to the end of every ".txt" file found in the current working directory. The script should run as a standalone command-line tool. For each target file, it should append the shared prompt text while preserving the file's existing content, using UTF-8 encoding throughout. After processing each file, it should report success with a clear status message showing the file name, and if an individual file cannot be updated, it should report the failure for that file with the reason and continue processing the remaining files rather than stopping. The script should not require any user input or arguments and should be safe to run repeatedly with clear, predictable output.
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
