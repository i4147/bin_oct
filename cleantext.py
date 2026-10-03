#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that takes a filename as an argument and removes invisible or control Unicode characters from the file's text, while preserving newline, carriage return, and tab characters.
The script should read the file as UTF-8, filter out characters whose Unicode category starts with "C" (control/format/other invisible categories), and overwrite the original file with the cleaned content.
It should print a success message when done, and handle errors gracefully by printing a friendly message if the file is not found or if any other exception occurs.
If no filename is provided as a command-line argument, print a usage instructions message instead."""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path


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
