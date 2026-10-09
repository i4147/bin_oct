#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that beautifies HTML files in place using BeautifulSoup's prettify method.
It should accept a list of file paths as command-line arguments, or if none are provided, recursively discover all ".html" files in the current working directory via a helper "get_files" function from a local "dh" module.
Each file should be read, parsed, and prettified, only rewriting the file if the formatted content differs from the original, with any errors during processing caught and printed without stopping the script.
Processing of multiple files should be handled concurrently using a helper "mpf" (map/multiprocess function) also imported from "dh", and the script should be runnable directly via a standard "__main__" entry point."""

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
