#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single website URL from the command line and saves the full rendered web page as a PDF file in the current working directory. If the user runs the script without providing a URL, it should print a short usage message showing the expected command format and exit with a non-zero status code.
The script should accept URLs with or without a scheme (for example, both "example.com" and "https://www.example.com/page" should be valid inputs). Before converting, normalize the input so that a missing scheme defaults to HTTP.
Name the output file automatically based on the website's host name: remove a leading "www." prefix, replace any character that is not a letter, digit, underscore, or hyphen with an underscore, and append the ".pdf" extension. If the host name cannot be determined, fall back to a generic name such as "website".
Perform the conversion using a reliable HTML-to-PDF approach capable of fetching and rendering the page at the given URL. When the conversion succeeds, print a single confirmation line in the form "Saved: <filename>.pdf". Handle errors gracefully: if the URL is unreachable or the conversion fails, display a clear, user-friendly error message and exit with a non-zero status code rather than showing a raw stack trace.
The script should be self-contained, runnable as a standalone command-line tool, and written with clean, readable code and sensible comments.
---"""

from __future__ import annotations
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
