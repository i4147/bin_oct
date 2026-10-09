#!/data/data/com.termux/files/usr/bin/env python

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
