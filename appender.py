#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that reads the contents of a text file named "prompt.txt" located in the user's home directory, using UTF-8 encoding.
The script should then find every ".txt" file in the current working directory, append the loaded text to the end of each of those files, and save the changes back to disk.
For each file processed, it should print a success message with a checkmark showing the filename, or if an error occurs while reading or writing a particular file, print a failure message with an X mark containing the filename and the exception details, without stopping the processing of the remaining files.
The script should execute this logic only when run as the main module."""

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
