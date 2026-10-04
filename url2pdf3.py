#!/data/data/com.termux/files/usr/bin/python3.12
import sys
from urllib.parse import urlparse


def url_to_filename(url: str) -> str:
    parsed = urlparse(url)

    if not parsed.scheme:
        url = f"http://{url}"
        parsed = urlparse(url)

    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]

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
