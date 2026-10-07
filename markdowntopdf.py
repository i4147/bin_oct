#!/data/data/com.termux/files/usr/bin/env python
"""Write a prompt for an AI coding agent to generate a Python 3.12 command-line script (intended to run under Termux on Android, using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that converts Markdown files into styled PDF documents using the `markdown` and `weasyprint` libraries.

The script's purpose is to batch-convert one or more Markdown files into PDF files, applying a custom CSS stylesheet (which may optionally be stored compressed as `.xz`) for styling, and supporting extended Markdown syntax via extensions.

Core requirements:

1. **Core conversion function** `md2pdf(pdf, raw=None, md=None, css=None, base_url=None, extras=None, extras_config=None)`:
   - Accepts either raw Markdown text (`raw`) or a path to a Markdown file (`md`, a `Path` object); if `md` is provided, read its text content (log this action at debug level).
   - Raise a custom `ValidationError` exception if there is no markdown content to process `raw` and `md`
   - Conv Python's `markdown` library, always including a base set of extensions: `markdown.extensions.tables`, `pymdownx.magiclink`, `pymdownx.betterem`, `pymdownx.superfences`, plus any additional extensions passed via `extras`, with optional per-extension configuration via `extras_config`.
   - Build a `weasyprint.HTML` object from the generated HTML string, using `base_url` (defaulting to the current working directory if not provided) for resolving relative resource paths (images, etc.).
   - If a `css` path is provided: if the file has a `.xz` suffix, decompress it in-memory using `lzma` (read as UTF-8 text) and construct a `weasyprint decory as its_url; otherwise load the CSS file directly by filename.
   - Render and write the final PDF to the given `pdf` output path, applying the collected stylesheet(s).

2. **Default CSS**: Define a default compressed stylesheet path constant pointing to `/sdcard/_static/css/markdown.css.xz` (for Termux/Android environments).

3. **CLI interface** (using `argparse`):
   - Accept one or more input Markdown file paths (positional arguments).
   - Support an option to specify an output PDF path or om extension with `.pdf`).
   - Support an option to specify a custom Cdefaulting to the default Cass extension configuration (e.g., Support a ver configures the `logging` module accordingly.
   - Process multiple input files concurrently using a `Threance.
   - Measure and log/print the total processing time using `time()`.
   - Handle errors gracefully (e.g., catch `ValidationError` and other exceptions per file) and report failures without crashing the whole batch, exiting with an appropriate non-zero status code via `sys.exit` when errors occur.

Use standard library modules (`argparse`, `json`, `logging`, `lzma`, `sys`, `pathlib.Path`, `concurrent.futures.ThreadPoolExecutor`, `time.time`) alongside the third-party `markdown` and `weasyprint` packages. Structure the code cleanly with a `logger` instance named after the module, clear function separation, and a `if __name__ == "__main__":` entry point that parses arguments and drives the batch conversion process.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/Cc3u7xeNnCnzLFfcPC83KL"""

import argparse
import json
import logging
import lzma
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
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
    extras_config = extras_config if extras_config else {}
    extras = extras if extras and len(extras) else []

    if md:
        logger.debug("Reading markdown content from file %s", md)
        raw = md.read_text()

    if raw is None or not len(raw):
        raise ValidationError("No markdown content to process (empty file or raw string)")

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
        raise ValidationError("Invalid input configuration string (should be valid JSON)") from err
    return parsed


def _convert_one(md_path, pdf_path, css=None, extras=None, extras_config=None):
    md2pdf(
        pdf_path,
        md=md_path,
        css=css,
        base_url=Path.cwd(),
        extras=extras if extras else None,
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

    extras = args.extras if args.extras else None
    if extras:
        print(f"🔧 Extras: {extras}")

    extras_config = None
    if args.config:
        extras_config = parse_config(args.config)
        print(f"🔧 Configuration: {extras_config}")

    convert_batch(args.workers, md_files, pdf, css, extras, extras_config)


if __name__ == "__main__":
    main()
