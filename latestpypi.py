#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that fetches the latest-updated packages feed from PyPI's public RSS feed, extracts the names of the listed Python packages, and saves them to a plain text file with one package name per line.
The script should:
- Retrieve the RSS feed over HTTPS from the PyPI packages feed URL, identifying itself with a custom user agent string and using a reasonable network timeout so it does not hang indefinitely.
- Parse the returned XML and iterate over each entry in the feed. For each entry, determine the package name by preferring the project path embedded in the entry's link; if no link is available, fall back to deriving the name from the entry's title by discarding the trailing version portion.
- Skip entries from which no name can be determined, and preserve the order in which packages appear in the feed.
- Write the collected names to a UTF-8 encoded text file named latest_pypi_packages.txt in the current working directory, with each name on its own line and a trailing newline at the end.
- Print a short confirmation message to the console after the file is written, indicating how many packages were saved.
- Handle the case where the feed is empty by still producing a valid (empty) output file.
The script should be self-contained, runnable from the command line with no arguments, and depend only on the Python standard library.
---"""

from __future__ import annotations
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

RSS_URL = "https://pypi.org/rss/packages.xml"
OUTPUT_FILE = Path("latest_pypi_packages.txt")


def fetch_latest_packages(url: str = RSS_URL) -> list[str]:
    req = urllib.request.Request(url, headers={"User-Agent": "pypi-latest-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    names: list[str] = []
    for item in root.findall("./channel/item"):
        title = item.findtext("title", default="").strip()
        link = item.findtext("link", default="").strip()
        name = ""
        if "/project/" in link:
            name = link.rstrip("/").rsplit("/project/", 1)[-1]
        elif title:
            name = title.rsplit(" ", 1)[0]
        if name:
            names.append(name)
    return names


def main() -> None:
    packages = fetch_latest_packages()
    OUTPUT_FILE.write_text("\n".join(packages) + "\n", encoding="utf-8")
    print(f"Saved {len(packages)} package names to {OUTPUT_FILE.resolve()}")
    for name in packages:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
