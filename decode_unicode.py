#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path from the command line, reads the file's raw bytes, and rewrites the file in place so that any backslash escape sequences in its text (such as \\n, \\t, \\\\, or \\uXXXX) are converted into their actual characters, saving the result as UTF-8 text. The script should accept the path as its first argument, trim surrounding whitespace from that argument, and handle the file so that it works from the command line as a simple utility. When finished, it should print a short confirmation message that includes the file path and states that the file was updated. Keep the tool minimal and focused on this single transformation, with clear behavior for a user who runs it on a text file containing escaped sequences.
---"""

from __future__ import annotations
from pathlib import Path
import sys

if __name__ == "__main__":
    path = Path(sys.argv[1].strip())
    text = path.read_bytes()
    decoded = text.encode("utf-8").decode("unicode_escape")
    path.write_text(decoded, encoding="utf-8")
    print(f"{path} updated")
