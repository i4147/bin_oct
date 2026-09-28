#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that takes a file path as a command-line argument, reads all lines from that file, and joins the non-empty lines together into a single continuous line by stripping their newline characters.
The script should then overwrite the original file with this concatenated content, appending a single trailing newline at the end.
It should use pathlib for file handling and read/write the file using UTF-8 encoding."""

from pathlib import Path
from sys import argv


def main() -> None:
    nl = ""
    with Path(argv[1]).open(encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                nl += line.strip("\n")
    Path(argv[1]).write_text(nl + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
