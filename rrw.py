#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that normalizes files either passed as arguments or discovered recursively via a helper module (dh.get_files/is_binary) starting from the current working directory, skipping binary files.
For Python (.py) files it parses the source into an AST and regenerates formatted code using astor, overwriting the file and printing a colored checkmark or cross symbol to indicate success or parse failure; for all other text files it applies Unicode NFD normalization and overwrites the file with the result.
Include an optional (currently disabled) backup mechanism that would save the original content to a ".bak" file before modification, and wrap file reading/writing in exception handling so errors are silently skipped."""

import ast
import sys
import unicodedata
from pathlib import Path
import astor
from dh import get_files, is_binary

BACKUP = False


def process_file(path) -> None:
    path = Path(path)
    if is_binary(path):
        return
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        if BACKUP:
            backup_file = path.with_suffix(path.suffix + ".bak")
            backup_file.write_text(content, encoding="utf-8")
        new_content = content
        if path.suffix == ".py":
            try:
                tree = ast.parse(content)
                new_content = astor.to_source(tree)
                path.write_text(new_content, encoding="utf-8")
                print(f"\x1b[0m[ \x1b[6;96m✓\x1b[0m ] {path.name} ")
                return
            except:
                print(f"\x1b[0m[ \x1b[6;96m✘\x1b[0m ] {path.name} ")
                return
        else:
            new_content = unicodedata.normalize("NFD", content)
            path.write_text(new_content, encoding="utf-8")
    except:
        return


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    sys.argv[2] if len(sys.argv) > 2 else False
    files = [Path(arg) for arg in args] if args else get_files(cwd)
    for path in files:
        process_file(path)


if __name__ == "__main__":
    raise SystemExit(main())
