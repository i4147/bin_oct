#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path from the command line and rewrites that file in place so that any hexadecimal escape sequences of the form backslash-x followed by two hex digits are replaced with the characters they represent. The script should read the file as raw bytes, attempt to decode them as UTF-8 while silently ignoring invalid byte sequences, and fall back to a permissive single-byte encoding if that decoding approach fails. It should then scan the text for these two-digit hex escapes, convert each valid match into its corresponding character, leave any match unchanged if its conversion is invalid, and save the transformed text back to the same file as UTF-8.
The script should validate its command-line usage: if the wrong number of arguments is supplied, it should print a brief usage message showing the expected invocation and exit without modifying anything. If the specified file does not exist, it should print a clear error message naming the file rather than crashing. For any other unexpected failure, it should print a concise error description. The program should run only when executed directly, not when imported as a module, and should be written so that its core conversion logic is reusable as a function.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys


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
