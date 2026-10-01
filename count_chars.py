#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that counts the total number of characters in a text file specified as a command-line argument.
The script should accept exactly one argument, the path to the input file, and print a usage message and exit with an error code if the argument count is incorrect.
It should open the file using UTF-8 encoding, read its full contents, compute the character count, and print a message showing the filename and the count.
If the specified file does not exist, it should catch the FileNotFoundError, print an appropriate error message, and exit with a non-zero status code."""

import sys
from pathlib import Path

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
