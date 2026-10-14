#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that compares two text files given as command-line arguments and reports how their contents differ at the line level. The script should accept two file paths, read both files as UTF-8 text, and handle the case where either file does not exist by printing a clear error message and exiting gracefully.
For each file, the script should report the total number of lines. It should then determine which lines in the first file do not appear anywhere in the second file, and which lines in the second file do not appear anywhere in the first, identifying each differing line by its 1-based line number. It should also count how many lines are common to both files, meaning lines whose content appears in both, regardless of position.
Trailing newline characters should be ignored when comparing lines, so that line content is judged on its visible text only. The script should print a concise summary showing each file's line count, the number of common lines, the count of distinct-to-file-1 and distinct-to-file-2 lines, and then list the specific line numbers that differ in each file. The output should be human-readable and easy to scan in a terminal.
The script should be a self-contained command-line tool that runs when executed directly, with a clear usage message if the expected arguments are missing.
---"""

from __future__ import annotations
from pathlib import Path
import sys


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
