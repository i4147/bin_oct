#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a text file path from the command line, with an optional second argument specifying a minimum line length (defaulting to 10 characters if omitted), and removes every line from that file whose content, after trimming surrounding whitespace, is shorter than the minimum length. The script should modify the file in place, keeping only the lines that meet or exceed the threshold while preserving their original order and line endings. It should read and write the file using UTF-8 encoding.
If the user runs the script without providing a filename, it should display a brief usage message showing the expected command format and exit with a non-zero status. If the specified file does not exist, it should print a clear error message naming the file and exit gracefully without crashing. For any other unexpected problem during reading or writing, it should print a concise error description instead of showing a raw traceback.
The script should be designed as a simple command-line utility that runs only when executed directly, not when imported as a module.
---"""

from __future__ import annotations
from pathlib import Path
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)
    fname = sys.argv[1]
    llen = int(str(sys.argv[2]).strip()) if len(sys.argv) == 3 else 10
    lines = []
    try:
        with Path(fname).open(encoding="utf-8") as f:
            lines = f.readlines()
        filtered = [line for line in lines if len(line.strip()) >= llen]
        with Path(fname).open("w", encoding="utf-8") as f:
            f.writelines(filtered)
    except FileNotFoundError:
        print(f"Error: File '{fname}' not found.")
    except Exception as e:
        print("An error occurred:", e)
