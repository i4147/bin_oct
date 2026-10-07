#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python 3.12 script (intended to run as a Termux executable on Android, using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that batch-converts reStructuredText (.rst) files into Markdown (.md) files, replacing the originals.

Requirements:

- Import helper utilities `get_files` and `mpf` from a local module named `dh` (`get_files` discovers files by extension in a directory; `mpf` runs a given function over a list of files, presumably in parallel/multiprocessing).
- Use `docutils.core.publish_parts` to convert RST content into HTML, using the "html" writer, with settings overrides: `initial_header_level=2`, `warning_stream=None`, and `report_level=5` (to suppress warnings). Extract and return the `html_body` part.
- If the RST-to-HTML conversion raises an exception, print a message in the form `"Conversion error details: {e}"` and re-raise the exception.
- Use `markdownify` (from the `markdownify` package) to convert the resulting HTML into Markdown text.
- Implement a `process_file(path)` function that: reads the given file's text as UTF-8, converts it from RST to HTML then to Markdown, writes the Markdown content to a new file with the same name but `.md` extension (UTF-8 encoding), and then deletes (unlinks) the original source file.
- Implement a `main()` function with no arguments that:
  - Gets the current working directory.
  - Reads command-line arguments (`sys.argv[1:]`); if arguments are provided, treat each as a file path (as a list of `Path` objects); if no arguments are provided, use `get_files(cwd, ext=[".rst"])` to discover all `.rst` files in the current directory.
  - If exactly one file is found/specified, process it directly by calling `process_file` on it, then exit the program with status code `1`.
  - Otherwise (zero or multiple files), pass the list of files to `mpf(process_file, files)` to process them (in parallel).
- Use `from __future__ import annotations` and standard type-friendly code structure suitable for Python 3.12.
- Guard execution with `if __name__ == "__main__": raise SystemExit(main())` so the script can be run directly from the command line, converting either specified files or all `.rst` files in the current directory.
- The script takes no required stdin input and produces no return value of significance from `main()` other than controlling the exit code in the single-file case; its main side effects are the creation of `.md` files and deletion of the original `.rst` files it processes.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/F4eZrYhitiaZ6UZtZcjD7Y"""

from __future__ import annotations
import sys
from pathlib import Path
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
