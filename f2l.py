#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that takes a filename as its first argument, reads the file line by line stripping whitespace, and wraps each line in double quotes (or single quotes if the line already contains a double quote).
It should join these quoted items with commas into a single brace-enclosed set-like string, e.g.
{"a", "b", "c"}, then overwrite the original file with this formatted content.
The script should also attempt to copy the resulting string to the clipboard using the termux-clipboard-set command, printing a success message if it works, or a warning suggesting to install termux-api if the command is not found."""

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
