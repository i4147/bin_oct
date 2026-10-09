#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script designed to run in a Termux environment (using the Termux Python 3.12 interpreter shebang) that converts a given webpage into a downloaded PDF file.

The script's purpose:
- Accept a single URL as a command-line argument.
- Convert the webpage at that URL into a PDF file using the `pdfkit` library.
- Automatically derive the output PDF filename from the website's domain name (hostname), rather than requiring the user to specify a filename.

Main inputs:
- A single required command-line argument: the target URL (e.g., `example.com` or `https://example.com/page`). The URL may or may not include a scheme (http/https); if missing, assume `http://` when parsing.

Main outputs:
- A PDF file saved in the current directory, named after the site's hostname (with any leading "www." removed, and any characters that aren't letters, digits, underscores, or hyphens replaced with underscores), with a `.pdf` extension.
- A printed confirmation message in the format `Saved: <filename>.pdf` after successful conversion.

Notable behavior and requirements:
- Include a function that extracts a clean, filesystem-safe "site name" from the URL: parse the hostname using `urlparse`, strip a leading "www." prefix, and sanitize any non-alphanumeric/underscore/hyphen characters by replacing them with underscores. Fall back to the generic name "website" if no hostname can be determined.
- If no URL argument is provided, print a usage message (`Usage: python script.py <url>`) and exit with a non-zero status code.
- Use `pdfkit.from_url()` to perform the actual URL-to-PDF conversion.
- Keep the script simple and self-contained as a single `main()` function plus the helper function, with a standard `if __name__ == "__main__":` entry point.
- The shebang line should target the Termux usr/bin Python 3.12 binary path (`#!/data/data/com.termux/files/usr/bin/python3.12`), indicating this is intended to be run as an executable script on Android/Termux.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/KcKhPj5y36F75obFt3bF8N"""

from __future__ import annotations
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

import pdfkit


def get_site_name(url):
    if "://" not in url:
        url = "http://" + url
    host = urlparse(url).hostname or "website"
    host = re.sub(r"^www\.", "", host)
    return re.sub(r"[^A-Za-z0-9_-]", "_", host)


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <url>")
        sys.exit(1)
    target_url = sys.argv[1]
    output_pdf = f"{get_site_name(target_url)}.pdf"
    pdfkit.from_url(target_url, output_pdf)
    print(f"Saved: {output_pdf}")


if __name__ == "__main__":
    main()
