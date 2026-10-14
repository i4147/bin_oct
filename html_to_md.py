#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that batch-converts HTML files into clean Markdown documents. The tool should take a collection of HTML files (provided via a file list or directory-based discovery) and, for each file, extract only the main readable article content while stripping away navigation, sidebars, advertisements, and other page boilerplate. The extracted content should then be converted into Markdown that preserves links, images, and tables, with no artificial line wrapping of long paragraphs.
Key behaviors:
- Skip any HTML file for which a corresponding Markdown file already exists, so repeated runs are safe and idempotent.
- Read HTML files using UTF-8 encoding, tolerating malformed bytes without crashing.
- Write each output Markdown file alongside its source file, using the same base name with a `.md` extension, also encoded as UTF-8.
- Provide informative console feedback: a success message showing the source and output file names when conversion succeeds, and a clear notice when no meaningful content could be extracted from a file.
- Optionally delete the original HTML file after a successful conversion, controlled by a configurable flag that defaults to enabled.
- Handle errors on a per-file basis so that a failure on one file is reported and does not stop processing of the remaining files.
- Return a result for each processed file indicating the resulting path and whether the conversion succeeded, so the caller can summarize outcomes.
- Accept file paths from the command line or from a supplied source of files, and run as a standalone script with a clear entry point.
The script should rely on established Python libraries of the implementer's choice for content extraction and HTML-to-Markdown conversion, and should use clean, readable, well-structured code with sensible error handling.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import get_files, mpf
import html2text
from readability import Document

remove_orig = True


def process_file(path: str | Path) -> tuple[Path, bool]:
    path = Path(path)
    md_file = path.with_suffix(".md")
    if md_file.exists():
        return (md_file, True)
    try:
        html_content = path.read_text(encoding="utf-8", errors="ignore")
        doc = Document(html_content)
        main_content = doc.summary()
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_tables = False
        h.body_width = 0
        markdown = h.handle(main_content)
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
    numf = len(files)
    if numf == 1:
        process_file(files[0])
        sys.exit(0)
    mpf(process_file, files)
