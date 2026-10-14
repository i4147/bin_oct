#!/data/data/com.termux/files/usr/bin/python
"""Write a Python command-line tool that takes a single website URL as its argument and saves a PDF snapshot of that web page to the current working directory. If the user runs the tool without providing a URL, it should print a brief usage message to the error output and exit with a non-zero status code. The URL may be supplied with or without a scheme (for example, "example.com" should be treated as "http://example.com"). The output filename should be derived from the site's domain: convert the domain to lowercase, drop any leading "www." prefix, replace every character that is not a letter, digit, hyphen, or underscore with an underscore, and append a ".pdf" extension. On success, the tool should print a confirmation message that includes the saved file's name and exit with a zero status. If the PDF generation fails for any reason, the tool should report a clear error message to the error output and exit with a non-zero status. The tool should be a single, self-contained script that can be run directly from the command line.
---"""

from __future__ import annotations
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
