#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
from pathlib import Path
import sys
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <filename> <prefix_string>", file=sys.stderr)
        sys.exit(1)
    fn = Path(sys.argv[1])
    str_to_add = sys.argv[2]
    if not fn.is_file():
        print(f"Error: {fn} does not exist or is not a file", file=sys.stderr)
        sys.exit(1)
    lines = fn.read_text().splitlines(keepends=True)
    newlines = [f"{str_to_add} {line}" if line.strip() else line for line in lines]
    fn.write_text("".join(newlines))
    print(f"{fn} updated")
