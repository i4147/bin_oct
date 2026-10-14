#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that fetches the latest package updates from the PyPI RSS feed, parses the, and presents the newly published or updated Python packages to the user in a clear, readable form. The script should retrieve the feed from the public PyPI packages RSS endpoint, handle network failures and malformed or unexpected feed structures gracefully by reporting errors to the standard error stream without crashing, and extract key details for each package entry, including its title, link, description, and publication date. It should present the results in an organized way, such as a concise list ordered from most to least recent, and should handle entries with missing fields by falling back to sensible placeholder values. Allow the user to optionally limit how many packages are displayed and to filter results by a keyword matched against package names or descriptions. Ensure the output is human-friendly, with timestamps formatted consistently, and that the script exits with an appropriate status code indicating success or failure.
---"""

from __future__ import annotations
from datetime import datetime
import sys
import xml.etree.ElementTree as ET
import requests

PYPI_RSS_URL = "https://pypi.org/rss/packages.xml"


def fetch_rss_feed(url: str) -> str | None:
    try:
        response = requests.get(url, timeout=55)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed: {e}", file=sys.stderr)
        return None


def parse_rss_feed(xml_content: str) -> list[dict[str, str]]:
    packages = []
    try:
        root = ET.fromstring(xml_content)
        channel = root.find("channel")
        if channel is None:
            print("Error: Invalid RSS format - no channel found", file=sys.stderr)
            return packages
        items = channel.findall("item")
        for item in items:
            package_info = {
                "title": item.findtext("title", "Unknown"),
                "link": item.findtext("link", "Unknown"),
                "description": item.findtext("description", "No description"),
                "pub_date": item.findtext("pubDate", "Unknown"),
                "guid": item.findtext("guid", "Unknown"),
            }
            title = package_info["title"]
            package_name = title.split()[0] if title else "Unknown"
            package_info["package_name"] = package_name
            packages.append(package_info)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error during parsing: {e}", file=sys.stderr)
    return packages


def display_packages(packages: list[dict[str, str]], limit: int | None = None):
    if not packages:
        print("No packages found in the RSS feed.")
        return
    display_packages = packages[:limit] if limit else packages
    print(f"\n{'=' * 40}")
    print(f"PyPI Latest Packages (Total: {len(packages)}, Showing: {len(display_packages)})")
    print(f"Fetched at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 40}\n")
    for i, pkg in enumerate(display_packages, 1):
        print(f"Package #{i}:")
        print(f"  Name:        {pkg['package_name']}")
        print(f"  Full Title:  {pkg['title']}")
        print(f"  Link:        {pkg['link']}")
        print(f"  Published:   {pkg['pub_date']}")
        print(
            f"  Description: {pkg['description'][:100]}..."
            if len(pkg["description"]) > 100
            else f"  Description: {pkg['description']}"
        )
        print(f"  GUID:        {pkg['guid']}")
        print("-" * 40)


def save_to_file(packages: list[dict[str, str]], filename: str = "pypi_packages.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"PyPI Latest Packages - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 40 + "\n\n")
            for i, pkg in enumerate(packages, 1):
                f.write(f"Package #{i}:\n")
                f.write(f"  Name:        {pkg['package_name']}\n")
                f.write(f"  Full Title:  {pkg['title']}\n")
                f.write(f"  Link:        {pkg['link']}\n")
                f.write(f"  Published:   {pkg['pub_date']}\n")
                f.write(f"  Description: {pkg['description']}\n")
                f.write(f"  GUID:        {pkg['guid']}\n")
                f.write("-" * 40 + "\n")
        print(f"\nPackages saved to '{filename}'")
    except OSError as e:
        print(f"Error saving to file: {e}", file=sys.stderr)


def main():
    limit = None
    save_output = False
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            if limit < 1:
                print("Error: Limit must be a positive number", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            if sys.argv[1] in ["--save", "-s"]:
                save_output = True
            else:
                print("Usage: python script.py [limit] [--save]")
                print("  limit: Number of packages to display (optional)")
                print("  --save or -s: Save output to file")
                sys.exit(1)
    if "--save" in sys.argv or "-s" in sys.argv:
        save_output = True
    print("Fetching PyPI RSS feed...")
    xml_content = fetch_rss_feed(PYPI_RSS_URL)
    if xml_content is None:
        sys.exit(1)
    packages = parse_rss_feed(xml_content)
    display_packages(packages, limit)
    if save_output:
        save_to_file(packages)
    print(f"\nSuccessfully extracted {len(packages)} packages from PyPI RSS feed.")


if __name__ == "__main__":
    raise SystemExit(main())
