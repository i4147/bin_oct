#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python 3.12 command-line script designed to run under Termux on Android (shebang: `#!/data/data/com.termux/files/usr/bin/python3.12`) that converts a given webpage URL into a saved PDF file.

Main behavior and requirements:

1. **Input**: The script takes a single command-line argument — a target URL (e.g., `example.com` or `https://example.com/page`). If no URL argument is provided, it should print a usage message (`Usage: python3 script.py <url>`) to stderr and exit with status code 1.

2. **Filename generation**: Implement a helper function `url_to_filename(url: str) -> str` that derives an output PDF filename from the URL's domain:
   - If the URL has no scheme (e.g., missing `http://`), prepend `http://` before parsing so the domain can be correctly extracted.
   - Parse the URL to extract the network location (domain), lowercase it.
   - Strip a leading `www.` prefix if present.
   - Sanitize the domain by replacing any character that is not alphanumeric, `-`, or `_` with `_`.
   - Return the sanitized domain name with a `.pdf` extension appended (e.g., `example_com.pdf`).

3. **PDF conversion**: Use the `pdfkit` library's `from_url` function to convert the target URL directly into a PDF file saved at the generated filename.

4. **Output/feedback**:
   - On success, print a confirmation message to stdout in the form `Saved PDF to <output_pdf>`.
   - On failure (any exception during PDF generation, e.g., missing `wkhtmltopdf` binary or network errors), catch the exception and write an error message to stderr in the form `Error creating PDF: <exception message>`, then return exit code 1.

5. **Structure**: Organize the logic into a `main(argv: list[str]) -> int` function that returns an integer exit code, and invoke it via `sys.exit(main(sys.argv))` in the `if __name__ == "__main__":` block, following standard CLI script conventions.

6. **Dependencies**: The script relies on the `urllib.parse.urlparse` function from the standard library and the third-party `pdfkit` package (which in turn requires the `wkhtmltopdf` binary installed on the system for actual PDF rendering).
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/Eutmfn8uD7F42dAJdAhGAN"""

from __future__ import annotations
from pathlib import Path
import sys
from urllib.parse import urlparse


def url_to_filename(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"http://{url}"
        parsed = urlparse(url)
    domain = parsed.netloc.lower()
    domain = domain.removeprefix("www.")
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in domain)
    return f"{safe}.pdf"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write("Usage: python3 script.py <url>\n")
        return 1
    target_url = argv[1]
    output_pdf = url_to_filename(target_url)
    try:
        import pdfkit

        pdfkit.from_url(target_url, output_pdf)
        print(f"Saved PDF to {output_pdf}")
    except Exception as exc:
        sys.stderr.write(f"Error creating PDF: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
