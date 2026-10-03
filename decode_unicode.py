#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that takes a file path as a command-line argument, reads the file's raw bytes, and decodes any literal escape sequences (such as \n, \t, or unicode escapes) into their actual characters using unicode_escape decoding.
The script should then overwrite the original file with the decoded text content using UTF-8 encoding, and finally print a confirmation message showing the file path followed by "updated".
The path argument should have surrounding whitespace stripped before use."""

import sys
from pathlib import Path

if __name__ == "__main__":
    path = Path(sys.argv[1].strip())
    text = path.read_bytes()
    decoded = text.encode("utf-8").decode("unicode_escape")
    path.write_text(decoded, encoding="utf-8")
    print(f"{path} updated")
