#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans an HTML document (provided as a file path given on the command line, or read from standard input) for embedded base64-encoded data URLs, such as inline images, fonts, or other assets, and extracts each one into a local output folder as a separate file. For every data URL found, the script should identify its MIME type, decode the base64 payload (tolerating whitespace and line breaks inside the encoded text, and skipping any entries that fail to decode without stopping the whole run), and save the result using a file extension appropriate to that MIME type. Output filenames should be derived from a short, stable hash of the decoded content so that identical assets are not duplicated and names remain unique. The script should create the output directory if it does not exist, report to the user how many assets were extracted and where they were saved, and handle common errors gracefully with clear messages (such as a missing input file or an unreadable HTML source). Keep the design simple, robust, and easy to run from a terminal, and rely on the standard library wherever practical, leaving the internal structure and implementation choices entirely to you.
---"""

from __future__ import annotations
import base64
import hashlib
from pathlib import Path
import re
import sys
from dh import MIME2EXT, get_nobinary

OUTPUT_DIR = Path("extracted_base64")
DATA_URL_RE = re.compile(r"data:(?P<mime>[-\w.+/]+);base64,(?P<data>[A-Za-z0-9+/=\s]+)", re.IGNORECASE)


def infer_extension(mime):
    return MIME2EXT.get(mime.lower(), mime.rsplit("/", maxsplit=1)[-1])[0]


def decode_base64(data):
    cleaned = "".join(data.split())
    return base64.b64decode(cleaned, validate=False)


def content_hash(data):
    return hashlib.sha256(data).hexdigest()[:15]


def extract_from_html(html):
    for matchz in DATA_URL_RE.finditer(html):
        mime = matchz.group("mime")
        raw_data = matchz.group("data")
        try:
            decoded = decode_base64(raw_data)
        except Exception:
            continue
        yield (mime, decoded)


def save_asset(mime, data):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ext = infer_extension(mime)
    digest = content_hash(data)
    filename = f"{digest}.{ext}"
    path = OUTPUT_DIR / filename
    if not path.exists():
        path.write_bytes(data)
    return path


def main():
    cwd = Path.cwd()
    seen_hashes = set()
    extracted_count = 0
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_nobinary(cwd)
    for html_file in files:
        try:
            html = html_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for mime, data in extract_from_html(html):
            digest = content_hash(data)
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            save_asset(mime, data)
            extracted_count += 1
    print(f"{extracted_count} elements extracted.")


if __name__ == "__main__":
    raise SystemExit(main())
