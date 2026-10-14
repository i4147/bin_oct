#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts the character encoding of a specified text file in place from ISO-8859-1 (Latin-1) to UTF-8. Before modifying anything, the script should create a backup copy of the original file, preserving its metadata, so the user can recover the original content if needed. The conversion should read the backup as Latin-1 text and rewrite the original file with the same content encoded as UTF-8. Once the conversion completes, the script should print a short confirmation message that names the converted file and the location of its backup. The target filename should be hardcoded to "script.sh" in the main entry point, so the script runs as a standalone tool when executed directly, but it should be structured so the conversion logic is reusable for any filename passed to it. Keep the script simple, dependency-free, and robust for typical text files.
---"""

from __future__ import annotations
import codecs
import shutil


def convert_in_place(filename):
    backup = f"{filename}.bak"
    shutil.copy2(filename, backup)
    with codecs.open(backup, "r", encoding="iso-8859-1") as f:
        content = f.read()
    with codecs.open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Converted {filename} (backup saved as {backup})")


if __name__ == "__main__":
    convert_in_place("script.sh")
