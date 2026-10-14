#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts HTML files into Markdown files. The script should accept one or more file paths and/or directory paths as command-line arguments. When a file path is given, it should be processed directly; when a directory path is given, it should discover all HTML files within that directory. If no arguments are provided, it should process all HTML files in the current working directory. Each HTML file should be read as UTF-8 text, converted into Markdown, and saved alongside the original file with the same base name and a `.md` extension. The conversion of multiple files should be performed in parallel to speed up batch processing. Ensure that the script handles the case where the Markdown output is not properly assigned or written, producing a correct Markdown file for every input. Keep the script simple, robust, and focused on this single purpose, and include clear error handling so that a failure on one file does not stop the processing of the others.
---"""

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
