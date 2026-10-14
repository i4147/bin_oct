#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a text file path as a command-line argument, reads the file line by line, trims surrounding whitespace from each line, and converts the lines into a single brace-enclosed, comma-separated list of quoted string items. For each line, use double quotes by default, but switch to single quotes if the line itself contains a double quote character, so the resulting literal remains valid. Overwrite the original file with this formatted output using UTF-8 encoding. Afterward, attempt to copy the formatted text to the system clipboard via the Termux clipboard utility; if that utility is not available, still keep the file update but notify the user that the clipboard feature requires installing the Termux API. On success, print a confirmation message that includes the file path and indicates the content was updated and copied. Handle the missing-clipboard case gracefully without crashing, and make the script runnable directly as a standalone program.
---"""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys


def main() -> None:
    fn = sys.argv[1]
    path = Path(fn)
    with path.open(encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    items = []
    for line in lines:
        quote_char = "'" if '"' in line else '"'
        items.append(f"{quote_char}{line}{quote_char}")
    formatted_content = "{" + ", ".join(items) + "}"
    path.write_text(formatted_content, encoding="utf-8")
    try:
        subprocess.run(
            ["termux-clipboard-set"],
            input=formatted_content,
            text=True,
            capture_output=True,
        )
        print(f"✓ Updated and copied: {path}")
    except FileNotFoundError:
        print(f"✓ File updated: {path}")
        print("⚠ Install termux-api for clipboard support")


if __name__ == "__main__":
    raise SystemExit(main())
