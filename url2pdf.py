#!/data/data/com.termux/files/usr/bin/python3.12
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
