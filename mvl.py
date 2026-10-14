#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that moves a specified range of lines from one text file to another from the command line. The tool should accept four inputs: a source file path, a starting line number, an ending line number (both inclusive and 1-based), and a destination file path. It should extract the requested block of lines from the source file, append those lines to the end of the destination file (creating the destination if it does not exist), and then remove those lines from the source file so that the source retains everything else in its original order.
Key behaviors to include:
- Handle line ranges gracefully: a start value below 1 should be treated as the beginning of the file, and an end value beyond the file's length should be clamped to the last line rather than causing an error.
- Read and write all files using UTF-8 encoding.
- Provide a clear success message summarizing which lines were moved and between which files.
- Report a friendly error message if the source file does not exist, and a general readable error message for any other failure, without crashing with an unhandled traceback.
- If the command-line arguments are missing or incorrect in number, print a short usage message showing the expected argument order and exit without performing any file changes.
- Run the logic only when the script is executed directly, not when it is imported as a module.
---"""

from __future__ import annotations
import sys


def move_lines(src_file: str, start_line: int, end_line: int, dest_file: str) -> None:
    try:
        with open(src_file, encoding="utf-8") as f:
            lines = f.readlines()
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        lines_to_move = lines[start_idx:end_idx]
        with open(dest_file, "a", encoding="utf-8") as f:
            f.writelines(lines_to_move)
        del lines[start_idx:end_idx]
        with open(src_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"Successfully moved lines {start_line}-{end_line} from {src_file} to {dest_file}.")
    except FileNotFoundError:
        print(f"Error: The file {src_file} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python move_lines.py <src_file> <start_line> <end_line> <dest_file>")
    else:
        src = sys.argv[1]
        start = int(sys.argv[2])
        end = int(sys.argv[3])
        dest = sys.argv[4]
        move_lines(src, start, end, dest)
