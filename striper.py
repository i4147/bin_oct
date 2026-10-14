#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single text file path from the command line and remov that file, overwriting the original file with the cleaned result. Each line in the output should be stored on its own line, with a consistent newline ending. The script should read and write the file using UTF-8 encoding. After processing, it should print a short confirmation message that includes the file name. If the specified file does not exist, it should print a clear error message naming the missing file instead of crashing. For any other unexpected problem during reading or writing, it should catch the error and print a readable description of what went wrong. The script should run its main behavior only when executed directly, not when imported as a module.
---"""

from __future__ import annotations
from pathlib import Path
from sys import argv


def remove_spaces_from_file(fname: str) -> None:
    try:
        with Path(fname).open(encoding="utf-8") as file:
            lines = file.readlines()
            cleaned_lines = [line.lstrip().strip().rstrip() for line in lines]
        with Path(fname).open("w", encoding="utf-8") as file:
            for k in cleaned_lines:
                file.writelines(k + "\n")
        print(f"{fname} cleaned.")
    except FileNotFoundError:
        print(f"Error: File '{fname}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    remove_spaces_from_file(argv[1])
