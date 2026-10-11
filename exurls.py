#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python command-line tool with the following specification:

Create a Python 3 command-line script for Termux (Android) that crawls a web page and extracts the hyperlinks it contains. The script should be runnable with a shebang line pointing to the Termux Python interpreter (`/data/data/com.termux/files/usr/bin/env python`) and use `from __future__ import annotations` for type hints. It must depend on the `requests` and `beautifulsoup4` (bs4) libraries, using the `html.parser` backend.

Functional requirements:

- Accept a URL as a required positional command-line argument, parsed with `argparse`. Provide additional options as needed to control the output file path and any other behavior the implementation requires.
- Build a `requests.Session` through a factory function that sets a realistic desktop browser User-Agent and matching headers: Accept (HTML/XHTML/XML with image/webp and a fallback wildcard), Accept-Language favoring English with Persian as a secondary option, Accept-Encoding of gzip, deflate, and br, Connection keep-alive, Upgrade-Insecure-Requests set to 1, and Cache-Control max-age=0.
- Fetch the target URL with a 30-second timeout, following redirects, and call `raise_for_status()` so HTTP errors surface as exceptions.
- Set the response encoding to the detected apparent encoding, falling back to UTF-8 when detection returns nothing.
- Parse the HTML with BeautifulSoup and collect every `<a>` tag that has an `href` attribute.
- Strip whitespace from each href. Skip empty hrefs, fragment-only links starting with `#`, and `javascript:` pseudo-links.
- Resolve each remaining href to an absolute URL relative to the page URL using `urljoin`.
- Parse the resolved URLs with `urlparse` and keep only those with an http or https scheme and a non-empty network location, so mailto, tel, data, and similar schemes are excluded.
- Deduplicate results using a set, then output the links in sorted order.
- Write the sorted links one per line to the output destination, and print a summary or the links to standard output as appropriate for the design.
- Optionally handle the output path as a `pathlib.Path`, creating parent directories if they do not exist.

Error handling and edge cases:

- Handle network failures, timeouts, and HTTP error statuses gracefully, reporting a clear message to standard error and exiting with a non-zero status code rather than printing a raw traceback.
- Handle a page with no qualifying links by reporting that no links were found, without crashing.
- Handle malformed or relative URLs, unusual schemes, and whitespace-padded hrefs as described above.
- Handle file write errors (permissions, invalid path) with a clear message and non-zero exit.
- Handle keyboard interrupt cleanly.

Execution: the script should be executable directly from the command line and exit with status 0 on success and a non-zero status on any failure. Include a `main()` function guarded by `if __name__ == "__main__":` and return an integer exit code from it passed to `sys.exit`. Use only the standard library plus `requests` and `beautifulsoup4`.
---"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from requests.sessions import Session


def create_session() -> Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    })
    return session


def extract_links(url: str, session: requests.Session):
    resp = session.get(url, timeout=30, allow_redirects=True)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag.get("href").strip()
        if href and not href.startswith("#") and not href.startswith("javascript:"):
            abs_url = urljoin(url, href)
            parsed = urlparse(abs_url)
            if parsed.scheme in {"http", "https"}:
                links.add(abs_url)
    for tag in soup.find_all(["video", "source", "iframe"], src=True):
        src = tag.get("src").strip()
        if src:
            abs_url = urljoin(url, src)
            parsed = urlparse(abs_url)
            if parsed.scheme in {"http", "https"}:
                links.add(abs_url)
    return sorted(links)


def split_internal_external(base_url, links):
    base_domain = urlparse(base_url).netloc
    internal = []
    external = []
    for link in links:
        if urlparse(link).netloc == base_domain:
            internal.append(link)
        else:
            external.append(link)
    return internal, external


def save_links(name: str, links) -> None:
    path = Path(name)
    content = "\n".join(links)
    path.write_text(content, encoding="utf-8")
    print(f"Saved {len(links)} links to {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and save all URLs from a webpage")
    parser.add_argument("url", nargs="?", help="Target URL")
    args = parser.parse_args()
    url = args.url or input("Enter URL: ").strip()
    if not url.startswith(("http://", "https://")):
        print("Error: URL must start with http:// or https://", file=sys.stderr)
        sys.exit(1)
    session = create_session()
    try:
        links = extract_links(url, session)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(
                "Access forbidden (403). The site may be blocking automated access.",
                file=sys.stderr,
            )
        else:
            print(f"HTTP error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to fetch or parse URL: {e}", file=sys.stderr)
        sys.exit(1)
    internal, external = split_internal_external(url, links)
    save_links("all_links.txt", links)
    if internal:
        save_links("internal.txt", internal)
    if external:
        save_links("external.txt", external)
    print(f"Total links: {len(links)} (Internal: {len(internal)}, External: {len(external)})")


if __name__ == "__main__":
    raise SystemExit(main())
