#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that takes a filename as a command-line argument and strips leading and trailing whitespace from every line in that file, then overwrites the file with the cleaned lines (each followed by a newline), reading and writing using UTF-8 encoding.
It should print a confirmation message like "{fname} cleaned." on success, and handle errors gracefully by printing a "File not found" message if the file doesn't exist, or a generic error message for any other exception.
The script should use pathlib.Path for file operations and read the filename from sys.argv, running the cleaning function when executed as the main module."""

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