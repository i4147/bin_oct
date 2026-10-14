#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that batch-converts local HTML files into Markdown documents. The tool should accept one or more file or directory inputs from the command line, locate all HTML files to process, and for each one produce a Markdown file with the same base name placed alongside it. Extraction should prioritize clean main-content extraction that preserves links, images, and tables, falling back to a more generic HTML-to-Markdown conversion when the primary method yields no usable output. Skip any file whose Markdown counterpart already exists so that repeated runs are safe and incremental. Read and write all files using UTF-8 encoding. Print a concise status message for each successful conversion showing the source and output filenames. Provide an optional flag that, when supplied, deletes the original HTML file only after its Markdown output has been successfully written. Handle empty or failed conversions gracefully by reporting them without crashing, and continue processing the remaining files. The script should be runnable from the command line and produce a clear summary of converted, skipped, and failed files at the end.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import get_files, mpf
import trafilatura

remove_orig = "-r" in sys.argv


def process_file(path: str | Path) -> tuple[Path, bool]:
    path = Path(path)
    md_file = path.with_suffix(".md")
    if md_file.exists():
        return md_file, True
    try:
        html_content = path.read_text(encoding="utf-8")
        markdown = trafilatura.extract(
            html_content,
            output_format="markdown",
            include_links=True,
            include_images=True,
            include_tables=True,
            no_fallback=False,
        )
        if not markdown:
            from bs4 import BeautifulSoup
            from markdownify import markdownify

            soup = BeautifulSoup(html_content, "html.parser")
            markdown = markdownify(str(soup))
        if markdown and markdown.strip():
            md_file.write_text(markdown, encoding="utf-8")
            print(f"✓ Converted: {path.name} -> {md_file.name}")
            if remove_orig:
                path.unlink()
            return md_file, True
        print(f"✗ No content extracted from {path.name}")
        return path, False
    except Exception as e:
        print(f"✗ Error processing {path.name}: {e}")
        return path, False


if __name__ == "__main__":
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = (
        [Path(p) for p in args if p.strip() != "-r"]
        if args and len(args) > 1
        else get_files(cwd, [".html", ".htm", ".xhtml", ".xhtm"])
    )
    numf = len(files)
    if numf == 1:
        process_file(files[0])
        sys.exit(0)
    mpf(process_file, files)
