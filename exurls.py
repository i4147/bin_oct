#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line tool that takes a target webpage URL as input, fetches its HTML using a requests Session configured with browser-like headers (User-Agent, Accept, Accept-Language, etc.) to avoid basic blocking, and parses it with BeautifulSoup to extract all absolute HTTP/HTTPS links found in anchor tags and other elements (such as scripts or media) with URL attributes, resolving relative URLs via urljoin and filtering out fragments and javascript: links.
It should use argparse to accept the URL (and likely options like output file or timeout) from the command line, deduplicate discovered links into a set, and output the resulting list of links, handling request errors gracefully with appropriate exit behavior via sys."""

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
