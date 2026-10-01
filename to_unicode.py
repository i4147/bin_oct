#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that takes a single filename argument and converts escaped hexadecimal byte sequences within the file into their corresponding readable characters.
The script should read the file as bytes, decode it using UTF-8 (falling back to Latin-1 if needed), then use a regular expression to find patterns like "\\xNN" and replace them with the actual character represented by that hex value.
The converted text should be written back to the same file, overwriting its original content.
It must handle a missing file by printing a "File not found" error, catch any other exceptions gracefully, and print a usage message if the filename argument is not provided."""

import re
import sys
from pathlib import Path


def convert_to_readable(filename: str) -> None:
    outfile = Path(filename)
    try:
        content = Path(filename).read_bytes()
        try:
            decoded_content = content.decode("utf-8", errors="ignore")
        except:
            decoded_content = content.decode("latin-1", errors="ignore")

        def replace_hex(m):
            try:
                return chr(int(m.group(1), 16))
            except ValueError:
                return m.group(0)

        readable_content = re.sub(r"\x([0-9a-fA-F]{2})", replace_hex, decoded_content)
        outfile.write_text(readable_content, encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_script.py <filename>")
    else:
        fname = sys.argv[1]
        convert_to_readable(fname)
