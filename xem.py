#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that scans one or more HTML (or other text) files for embedded base64-encoded data URLs (e.g., "data:image/png;base64,...") using a regex, decodes each match, and saves the decoded binary content as separate files into an "extracted_base64" output directory.
Filenames should be derived from a short SHA-256 hash of the decoded content plus a file extension inferred from the MIME type (via a MIME2EXT mapping), skipping duplicates already saved.
The script should accept file paths as command-line arguments, or if none are given, default to non-binary files discovered in the current working directory via a helper function get_nobinary.
It should track and report the count of successfully extracted assets, gracefully skip files that fail to decode or read, and avoid re-writing files whose content hash already exists on disk."""

from __future__ import annotations
import base64
import hashlib
from pathlib import Path
import re
import sys

from dh import MIME2EXT, get_nobinary


OUTPUT_DIR = Path("extracted_base64")
DATA_URL_RE = re.compile("data:(?P<mime>[-\\w.+/]+);base64,(?P<data>[A-Za-z0-9+/=\\s]+)", re.IGNORECASE)


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
