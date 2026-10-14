#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line utility for decoding Unicode escape sequences found in text files. When run with no arguments, it should scan the current working directory and process all non-binary text files it finds. When given one or more arguments, each argument may be a file path or a directory path: individual non-binary files are processed directly, and directories are expanded to include the non-binary files they contain. For each non-binary file, read its contents as UTF-8 text and treat every non-empty line as a hexadecimal Unicode code point fragment (for example, a value such as "1F600" or "00E9"). For each such line, output two results to standard output: first, the original line in its escaped form, prefixed so it reads as a \\u-style escape; second, the decoded character or characters that the escape represents. Ensure the decoding is robust to malformed input, so that invalid entries do not crash the program and are reported clearly to the user instead. Skip binary files entirely, and make sure files that cannot be read are handled gracefully with a helpful message. The script should exit cleanly with a status code of zero on success and a non-zero status code on fatal errors. Keep the output readable, with each original value and its decoded result easy to distinguish, and include a brief usage message if the user requests help or supplies invalid arguments.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import get_nobinary, is_binary


def unicode_unescape(text: str) -> str:
    return bytes(text, "utf-8").decode("unicode_escape")


def process_file(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    path = Path(path)
    for line in lines:
        nl = r"\u" + str(line.strip())
        decoded = unicode_unescape(nl)
        print(nl)
        print(decoded)


def main() -> None:
    args = sys.argv[1:]
    cwd = Path.cwd()
    files = []
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file() and (not is_binary(p)):
                files.append(p)
            if p.is_dir():
                files.extend(get_nobinary(p))
    else:
        files = get_nobinary(cwd)
    for f in files:
        process_file(f)


if __name__ == "__main__":
    raise SystemExit(main())
