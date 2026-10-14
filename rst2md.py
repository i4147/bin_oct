#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts reStructuredText (.rst) documentation files into Markdown (.md) files. The tool should accept one or more file paths as command-line arguments; if no arguments are given, it should automatically find all .rst files in the current working directory and process them. For each input file, read its content as UTF-8 text, convert the reStructuredText into HTML body content while suppressing noisy warnings and reporting only genuine conversion errors (printing a clear message and stopping on failure), then convert that HTML into Markdown. Write the resulting Markdown to a new file that keeps the original file's name and location but uses the .md extension, encoded as UTF-8. After a successful conversion, remove the original .rst file so that it is replaced by the Markdown version. Handle the case where a single file is processed as the core workflow, and design the behavior so it is robust, readable, and easy to run from the command line.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import get_files, mpf
from docutils.core import publish_parts
from markdownify import markdownify


def rst_to_html(content: str) -> str:
    try:
        parts = publish_parts(
            source=content,
            writer_name="html",
            settings_overrides={
                "initial_header_level": 2,
                "warning_stream": None,
                "report_level": 5,
            },
        )
        html_content = parts["html_body"]
        return html_content
    except Exception as e:
        print(f"Conversion error details: {e}")
        raise


def process_file(path):
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    html_content = rst_to_html(content)
    md_content = markdownify(html_content)
    md_path = path.with_suffix(".md")
    md_path.write_text(md_content, encoding="utf-8")
    path.unlink()


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".rst"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
