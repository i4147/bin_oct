#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that batch-converts reStructuredText (.rst) files into HTML using docutils, replacing each original file with an equivalent .html file.
It should accept file paths as command-line arguments, or if none are given, discover all .rst files in the current working directory via a helper function get_files from a module named dh.
For each file, it reads the RST content, converts it to HTML body content (suppressing warnings and using initial header level 2), writes the result to a new file with the same name but .html extension, and then deletes the original .rst file.
If exactly one file is processed, the script exits with status code 1; otherwise it processes all files and exits normally.
Conversion errors should be caught, logged with a descriptive message, and re-raised."""

import sys
from pathlib import Path
from dh import get_files
from docutils.core import publish_parts


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
    html_path = path.with_suffix(".html")
    html_path.write_text(html_content, encoding="utf-8")
    path.unlink()


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".rst"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    for f in files:
        process_file(f)


if __name__ == "__main__":
    raise SystemExit(main())
