#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python 3.12 command-line script designed to run in a Termux environment (using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that converts a web page into a PDF file using the `weasyprint` library.

The script must define a function `convert_url_to_pdf(url: str, output_filename: str)` that:
- Prints a status message indicating it is fetching and converting the given URL.
- Uses WeasyPrint's `HTML` class to load the content from the URL and calls `write_pdf()` to render and save it as a PDF to the specified output filename.
- Wraps the conversion logic in a try/except block: on success, prints a confirmation message showing the saved PDF filename; on failure, catches any exception and prints an error message (including the exception details) to standard error (`sys.stderr`) rather than raising it.

In the `if __name__ == "__main__":` block, hardcode a target URL variable set to `"https://example.com"` and an output filename variable set to `"website_snapshot.pdf"`, then call `convert_url_to_pdf` with these two values.

Import only `sys` and `HTML` from `weasyprint`. Keep the script simple, with no command-line argument parsing — the URL and output filename are fixed constants in the script.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/a3bQdoF7kFLQM5Zwoc9Fsk"""

from __future__ import annotations
from pathlib import Path
import sys

from weasyprint import HTML


def convert_url_to_pdf(url: str, output_filename: str):
    print(f"Fetching and converting: {url}...")
    try:
        HTML(url).write_pdf(output_filename)
        print(f"Success! PDF saved as '{output_filename}'")
    except Exception as e:
        print(f"An error occurred during conversion: {e}", file=sys.stderr)


if __name__ == "__main__":
    target_url = "https://example.com"
    output_pdf = "website_snapshot.pdf"
    convert_url_to_pdf(target_url, output_pdf)
