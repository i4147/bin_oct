#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line script that accepts file and/or directory paths as arguments (defaulting to the current working directory if none are given), and gathers a list of text files to process using helper functions `get_nobinary` and `is_binary` from a local module named `dh` to skip binary files.
For each collected file, read it line by line, strip whitespace, prepend the string "\\u" to each line to form a unicode escape sequence, decode it into the actual unicode character using UTF-8 bytes and the "unicode_escape" codec, and print both the raw escaped string and its decoded result to standard output.
The script should be runnable as a module with `sys.exit`/`SystemExit` returning the result of a `main()` function."""

import sys
from pathlib import Path
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
