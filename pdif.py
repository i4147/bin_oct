#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that compares the contents of two text files given as arguments.
It should read both files line by line (handling missing files gracefully with an error message), then determine how many lines are common between them and identify the line numbers in each file whose content does not appear in the other file.
The script should print the total line counts for each file, the number of common lines, and the count plus line numbers of differing lines for both files.
It must require exactly two command-line arguments (the file paths) and show a usage message if the argument count is wrong."""

from __future__ import annotations

import sys
from pathlib import Path


def compare_files(file1: str, file2: str) -> None:
    try:
        with (
            Path(file1).open("r", encoding="utf-8") as f1,
            Path(file2).open("r", encoding="utf-8") as f2,
        ):
            lines1 = f1.readlines()
            lines2 = f2.readlines()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    lines1 = [line.rstrip("\n") for line in lines1]
    lines2 = [line.rstrip("\n") for line in lines2]
    diff_lines_1 = []
    diff_lines_2 = []
    common_count = 0
    for i, line in enumerate(lines1):
        if line not in lines2:
            diff_lines_1.append(i + 1)
    for i, line in enumerate(lines2):
        if line not in lines1:
            diff_lines_2.append(i + 1)
    for line in lines1:
        if line in lines2:
            common_count += 1
    print(f"{file1} : {len(lines1)}")
    print(f"{file2} : {len(lines2)}")
    print(f"common: {common_count}")
    print(f"Number of different lines in File 1: {len(diff_lines_1)}")
    if diff_lines_1:
        print(f"Line numbers: {diff_lines_1}")
    print(f"Number of different lines in File 2: {len(diff_lines_2)}")
    if diff_lines_2:
        print(f"Line numbers: {diff_lines_2}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <file1> <file2>")
        sys.exit(1)
    compare_files(sys.argv[1], sys.argv[2])
