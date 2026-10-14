#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that batch-converts HTML files into clean Markdown documents. The tool should accept a directory or a set of file paths, locate HTML files within them, and for each file extract only the main readable article content (stripping navigation, ads, sidebars, and boilerplate), then convert that content into Markdown and save it alongside the original file using the same base name with a .md extension.
Key behaviors:
- Skip any file for which a Markdown counterpart already exists, reporting it as already processed rather than reprocessing it.
- Read input files tolerantly, ignoring or replacing undecodable characters so that malformed HTML does not halt processing.
- Only write the Markdown output if meaningful text was extracted; if the result is empty or whitespace-only, report that no content could be extracted and leave the source untouched.
- Provide a configurable option to delete the original HTML file after a successful conversion, enabled by default.
- Handle errors per file so that a failure on one document is reported with a clear message and does not stop processing of the remaining files.
- Print a concise, human-readable status line for each file: a success indicator with the converted filenames, a warning for files with no extractable content, and an error indicator with the reason for failures.
- When run from the command line with no arguments, default to processing the current working directory; otherwise process the paths supplied by the user.
- Return a clear result for each processed file indicating the resulting output path and whether the conversion succeeded, so the results can be summarized at the end (e.g., total converted, skipped, and failed).
- Target UTF-8 output and preserve the original text's encoding and characters in the Markdown.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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
