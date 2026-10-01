#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that batch-converts HTML files into Markdown using readability-lxml to extract the main article content and markdownify to convert it to Markdown.
It should accept file paths as command-line arguments, or if none are given, discover all HTML/HTM/XHTML files in the current directory via a helper function, skipping any file that already has a corresponding .md output.
For each file it should read the HTML, extract the readable main content, convert it to Markdown, write the result next to the original with a .md extension, delete the original source file after a successful conversion, and print a success or failure message per file; a single file should be processed directly while multiple files should be processed in parallel via a multiprocessing helper."""

import sys
from pathlib import Path
from dh import get_files, mpf
from markdownify import markdownify as md
from readability import Document

remove_orig = True


def process_file(path) -> tuple[Path, bool]:
    path = Path(path)
    md_file = path.with_suffix(".md")
    if md_file.exists():
        return (md_file, True)
    try:
        html_content = path.read_text(encoding="utf-8", errors="ignore")
        doc = Document(html_content)
        main_content = doc.summary()
        markdown = md(main_content)
        if markdown and markdown.strip():
            md_file.write_text(markdown, encoding="utf-8")
            print(f"✓ Converted: {path.name} -> {md_file.name}")
            if remove_orig:
                path.unlink()
            return (md_file, True)
        print(f"✗ No content extracted from {path.name}")
        return (path, False)
    except Exception as e:
        print(f"✗ Error: {e}")
        return (path, False)


if __name__ == "__main__":
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".html", ".htm", ".xhtml", ".xhtm"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    mpf(process_file, files)
