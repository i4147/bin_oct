#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path from the command line, reads the file's contents as UTF-8 text, and reports the total number of characters it contains. The script should print a clear message that includes the file name and the character count. If the user does not supply exactly one argument, the script should print a brief usage message showing how to run it and exit with a non-zero status. If the specified file does not exist, the script should print a clear, user-friendly error message naming the missing file and exit with a non-zero status. The script should run only when executed directly, not when imported as a module.
---"""

from __future__ import annotations
from pathlib import Path
import sys

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python count_chars_of_input_file.py <input_file>")
        sys.exit(1)
    input_file = sys.argv[1]
    try:
        with Path(input_file).open(encoding="utf-8") as file:
            content = file.read()
            char_count = len(content)
            print(f"Number of characters in '{input_file}': {char_count}")
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
