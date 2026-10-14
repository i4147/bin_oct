#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that formats HTML files in place so they are consy to read. The script should optional list of file paths from the command line. If no pa, it should automatically find all HTML files in the current working directory and process them. Each HTML file should be read as UTF-8 text, reformatted into a standardized, indented layout using an HTML parser that tolerates imperfect markup, and saved back to the same file only when the formatted output actually differs from the original content, so unchanged files are left untouched. The processing should run across multiple files in parallel to keep it error occurs while handling any single file (such as an unreadable file or encoding problem), the script should print a clear message identifying the file and the problaining files without crashing. The script should be-contained command-line utility with a clear entry point, and it should produce no output other than error messages for files that fail.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from bs4 import BeautifulSoup
from dh import get_files, mpf


def process_file(path) -> bool:
    try:
        with open(path, encoding="utf-8") as file:
            content = file.read()
        soup = BeautifulSoup(content, "html.parser")
        beautified_content = soup.prettify()
        if content != beautified_content:
            with open(path, "w", encoding="utf-8") as file:
                file.write(beautified_content)
    except Exception as e:
        print(f"Error beautifying HTML file {path}: {e}")
        return False
    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    cwd = Path.cwd()
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".html"])
    mpf(process_file, files)
