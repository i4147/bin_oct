#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that converts HTML files to Markdown files in place, using the `markdownify` library to perform the conversion and helper functions `get_files` and `mpf` from a local `dh` module for file discovery and multiprocessing execution.
For each input HTML file, the script should read its content, convert it to Markdown, and write the result to a new file with the same base name but a `.md` extension.
It should accept command-line arguments that can be individual file paths or directory paths; for directories, it should recursively collect all `.html` files, and if no arguments are given it should default to scanning the current working directory.
The discovered files should then be processed in parallel via the `mpf` utility."""

from __future__ import annotations
from pathlib import Path
import sys

from dh import get_files, mpf
from markdownify import markdownify


def process_file(path) -> None:
    path = Path(path)
    md_path = path.with_suffix(".md")
    content = path.read_text(encoding="utf8")
    markdownify(content)
    md_path.write_text(md_content, encoding="utf-8")


if __name__ == "__main__":
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = []
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(get_files(p, ext=[".html"]))
    else:
        files.extend(get_files(p, ext=[".html"]))
    mpf(process_file, files)
