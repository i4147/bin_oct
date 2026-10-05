#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python 3.12 command-line script (intended to run under Termux on Android, using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that batch-converts reStructuredText (`.rst`) files into Markdown (`.md`) files, replacing the originals.

Main behavior and requirements:

1. **Imports/dependencies**: Use `docutils.core.publish_parts` to convert RST content to HTML, and `markdownify` (the `markdownify` function) to convert that HTML into Markdown. Also import two helper utilities from a local module named `dh`: `get_files` (to discover files by extension in a directory) and `mpf` (a multiprocessing/parallel-processing helper that applies a function to a list of files).

2. **RST to HTML conversion function** (`rst_to_html`): string of RST content and returns the HTML body string.
   - Calls `publish_parts` with `writer_name="html"`, and `settings_overrides` setting `initial_header_level` to 2, `warning_stream` to `None`, and `report_level` to 5 (suppress warnings/errors from being printed).
   - Returns `parts["html_body"]`.
   - Wraps the conversion in a try/except that prints an error message (`"Conversion error details: {e}"`) and re-raises the exception on failure.

3. **Single file processing function** (`process_file`):
   - Accepts a file path (string or Path).
   - Reads the file's text content as UTF-8.
   - Converts the content from RST to HTML using `rst_to_html`, then from HTML to Markdown using `markdownify`.
   - Writes the resulting Markdown to a new file with the same name but `.md` extension (using `Path.with_suffix(".md")`), encoded as UTF-8.
   - Deletes (unlinks) the original `.rst` file after successful conversion.

4. **Main entry point** (`main`):
   - Determines the current working directory.
   - If command-line arguments are provided, treats each argument as a file path to process; otherwise, uses `get_files` to automatically discover all `.rst` files in the current working directory.
   - If exactly one file is found/specified, processes it directly via `process_file` and exits with status code `1`.
   - If multiple files are found/specified, processes them in parallel using the `mpf` helper function, passing `process_file` and the list of files.
   - The script should be runnable as a standalone executable, with `main()` invoked via `raise SystemExit(main())` inside the `if __name__ == "__main__":` block.

The overall purpose is a quick utility/tool for bulk-converting RST documentation files to Markdown format, intended for personal/local use (e.g., a Termux/Android environment), either on files passed as arguments or on all `.rst` files found in the current directory, with automatic cleanup of the original `.rst` files after conversion.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/mbmV4rw8etbdkqNfayVsCz"""

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
