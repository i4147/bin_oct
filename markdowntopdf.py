#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts Markdown content into a styled PDF document. The tool should accept its input either from a Markdown file on disk or from a raw Markdown string passed directly, and it should write the rendered result to a specified PDF output path.
Core behavior:
- Convert Markdown to HTML, supporting common extensions such as tables, auto-linked URLs, improved emphasis handling, and fenced code blocks, with the ability to enable additional user-specified Markdown extensions and pass per-extension configuration options.
- Validate input: if no Markdown content is provided or the content is empty, fail with a clear, dedicated validation error.
- Apply styling through a CSS stylesheet. By default, use a bundled, compressed (xz-compressed) stylesheet located at a known default path, and allow the user to supply a custom CSS file instead.
- Resolve relative resources (images, links) against an optional base URL or the input file's location so they render correctly in the PDF.
- Produce a PDF file at the requested output location, creating the output as needed.
Command-line interface:
- Accept an input Markdown file path or raw Markdown text, an output PDF path, an optional custom CSS file, an optional base URL, a list of extra Markdown extensions, and optional JSON-formatted extension configuration.
- Provide a verbosity option to control logging detail.
- Support batch processing of multiple Markdown files in parallel, with each file converted to a corresponding PDF.
- Report errors clearly to the user and exit with a non-zero status code on failure; exit with zero on success.
Quality expectations:
- Handle malformed JSON configuration and missing files gracefully with helpful messages.
- Log progress and key steps at appropriate levels, and include timing information for conversions.
- Keep the script self-contained, readable, and organized into well-separated functions, with a docstring-style description of its usage.
---"""

from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import lzma
from pathlib import Path
import sys
from time import time
from markdown import markdown
from weasyprint import CSS, HTML

MARKDOWN_BASE_EXTENSIONS = [
    "markdown.extensions.tables",
    "pymdownx.magiclink",
    "pymdownx.betterem",
    "pymdownx.superfences",
]
DEFAULT_CSS = Path("/sdcard/_static/css/markdown.css.xz")
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


def md2pdf(pdf, raw=None, md=None, css=None, base_url=None, extras=None, extras_config=None):
    extras_config = extras_config or {}
    extras = extras if extras and len(extras) else []
    if md:
        logger.debug("Reading markdown content from file %s", md)
        raw = md.read_text()
    if raw is None or not len(raw):
        msg = "No markdown content to process (empty file or raw string)"
        raise ValidationError(msg)
    extensions = MARKDOWN_BASE_EXTENSIONS + extras
    raw_html = markdown(raw, extensions=extensions, extension_configs=extras_config)
    if base_url is None:
        base_url = Path.cwd()
    html = HTML(string=raw_html, base_url=str(base_url))
    styles = []
    if css:
        css_path = Path(css)
        if css_path.suffix == ".xz":
            with lzma.open(css_path, "rt", encoding="utf-8") as f:
                css_text = f.read()
            styles.append(CSS(string=css_text, base_url=str(css_path.parent)))
        else:
            styles.append(CSS(filename=str(css_path)))
    html.write_pdf(pdf, stylesheets=styles)


def parse_config(config):
    try:
        parsed = json.loads(config)
    except json.decoder.JSONDecodeError as err:
        msg = "Invalid input configuration string (should be valid JSON)"
        raise ValidationError(msg) from err
    return parsed


def _convert_one(md_path, pdf_path, css=None, extras=None, extras_config=None):
    md2pdf(
        pdf_path,
        md=md_path,
        css=css,
        base_url=Path.cwd(),
        extras=extras or None,
        extras_config=extras_config,
    )


def convert_batch(workers, md_files, pdf=None, css=None, extras=None, extras_config=None):
    started_at = time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = []
        for md_path in md_files:
            pdf_path = md_path.with_suffix(".pdf") if pdf is None else pdf
            futures.append(pool.submit(_convert_one, md_path, pdf_path, css, extras, extras_config))
        for f in futures:
            f.result()
    print(f"🚀 Output files generated in {(time() - started_at):.3f}s")


def main():
    parser = argparse.ArgumentParser(prog="md2pdf", usage="python md2pdf.py readme.md")
    parser.add_argument("md", nargs="*", help="Markdown input file(s)")
    parser.add_argument("-o", "--output", help="PDF output file (only with single input)")
    parser.add_argument("--css", help="CSS file to style the PDF (supports .xz)")
    parser.add_argument("--extras", nargs="*", help="Extra markdown extensions")
    parser.add_argument("--config", help="JSON configuration for extensions")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker threads (default: 4)")
    args = parser.parse_args()
    if not args.md:
        print("🤷‍♂️ No markdown input file. See `--help`")
        sys.exit(2)
    md_files = [Path(f) for f in args.md]
    pdf = Path(args.output) if args.output else None
    if pdf is not None and len(md_files) > 1:
        print("❌ PDF output option `--output/-o` cannot be used with multiple input.")
        sys.exit(2)
    if args.css:
        css = Path(args.css)
    else:
        css = DEFAULT_CSS if DEFAULT_CSS.exists() else None
    if css:
        print(f"💅 CSS file: {css}")
    extras = args.extras or None
    if extras:
        print(f"🔧 Extras: {extras}")
    extras_config = None
    if args.config:
        extras_config = parse_config(args.config)
        print(f"🔧 Configuration: {extras_config}")
    convert_batch(args.workers, md_files, pdf, css, extras, extras_config)


if __name__ == "__main__":
    main()
