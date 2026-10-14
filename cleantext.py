#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path from the command line and removes invisible or non-printable control characters from a UTF-8 encoded text file, while preserving normal line breaks and tabs. The script should read the file, strip out any characters belonging to Unicode control or format categories except newline, carriage return, and tab, and then overwrite the original file in place with the cleaned content. It should print a short confirmation message when the cleaning succeeds. If no filename argument is provided, it should display a brief usage message instead of doing anything else. If the specified file does not exist, it should report a clear error message without crashing. Any other unexpected error should be caught and reported with a readable description. The script should be runnable directly from the terminal as a standalone tool.
---"""

from __future__ import annotations
from pathlib import Path
import sys
import unicodedata


def clean_file(filename: str) -> None:
    try:
        with Path(filename).open(encoding="utf-8") as f:
            lines = f.readlines()
        cleaned_lines = []
        for line in lines:
            cleaned_line = "".join(ch for ch in line if unicodedata.category(ch)[0] != "C" or ch in "\n\r\t")
            cleaned_lines.append(cleaned_line)
        with Path(filename).open("w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)
        print(f"Successfully cleaned: {filename}")
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_text.py <filename>")
    else:
        target_file = sys.argv[1]
        clean_file(target_file)
