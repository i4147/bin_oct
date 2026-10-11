#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that asks an AI coding agent to recreate a Python module implementing a class for searching English subtitles on OpenSubtitles.

Create a single-file Python 3 script (intended to run under Termux on Android, so include the Termux-style shebang line `#!/data/data/com.termux/files/usr/bin/env python`) that defines a `SubtitleDownloader` class for searching subtitles on the OpenSubtitles REST API.

Requirements:

**Purpose:** The script provides a downloader helper that searches OpenSubtitles for English-language subtitles matching a free-text query, such as a movie or show name or a release filename.

**Imports and dependencies:**
- Use `from __future__ import annotations` at the top.
- Use the standard library modules `re` and `sys`, and `quote` from `urllib.parse`.
- Use the third-party `requests` library for HTTP.

**Class `SubtitleDownloader`:**
- The constructor creates a `requests.Session` stored on `self.session`, and sets its headers to include a browser-like User-Agent string: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36`.
- A method `search_opensubtitles(self, query)` performs the search:
  - Normalize the query by replacing underscores and periods with spaces.
  - Send a GET request to `https://rest.opensubtitles.com/api/v1/subtitles` with the query parameters `query` (the normalized string), `languages` set to `en`, and `type` set to `all`. Use the session for the request.
  - If the HTTP status is 200, parse the JSON body. If the `data` key is present and non-empty, iterate through its items. Each item has an `attributes` object (default to an empty dict if missing). Return the first item whose `attributes.language` equals `en`, as a dictionary with keys:
    - `id`: the item's `id` (required; use direct key access)
    - `title`: the attribute `title`, defaulting to the original (un-normalized) query string
    - `url`: the attribute `url` (may be None)
    - `files`: the attribute `files`, defaulting to an empty list
  - If no matching English item is found, or the status is not 200, or `data` is empty, return `None`.
  - Wrap the whole operation in a try/except that catches any `Exception`, prints `Error searching OpenSubtitles: <error>` to standard output, and returns `None`.

**Behavior notes and edge cases:**
- No timeout, retry, or authentication headers are specified; the API key is not used in this version.
- The method does not raise exceptions to callers; all failures result in `None`.
- The `re`, `sys`, and `quote` imports are present in the original module; include them even though this portion does not need to use them, so the module matches the original structure.
- The script has no `main` block or CLI in this portion; it only defines the class so it can be imported or extended.

**Output expectations:** Produce only the complete Python file content, with the shebang, imports, and class as described, following standard PEP 8 style and a 4-space indent.
---"""

from __future__ import annotations

import re
import sys
from urllib.parse import quote

import requests


class SubtitleDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

    def search_opensubtitles(self, query):
        try:
            search_query = query.replace("_", " ").replace(".", " ")
            url = "https://rest.opensubtitles.com/api/v1/subtitles"
            params = {"query": search_query, "languages": "en", "type": "all"}
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    for item in data["data"]:
                        attrs = item.get("attributes", {})
                        if attrs.get("language") == "en":
                            return {
                                "id": item["id"],
                                "title": attrs.get("title", query),
                                "url": attrs.get("url"),
                                "files": attrs.get("files", []),
                            }
            return None
        except Exception as e:
            print(f"Error searching OpenSubtitles: {e}")
            return None

    def download_from_opensubtitles(self, sub_info):
        try:
            if sub_info and sub_info.get("files"):
                for file_info in sub_info["files"]:
                    if file_info.get("file_name", "").endswith(".srt"):
                        download_url = file_info.get("url")
                        if download_url:
                            response = self.session.get(download_url)
                            if response.status_code == 200:
                                return response.text
            return None
        except Exception as e:
            print(f"Error downloading from OpenSubtitles: {e}")
            return None

    def search_yify_subtitles(self, query):
        try:
            query = query.replace("_", " ").replace(".", " ")
            search_url = f"https://yts.mx/api/v2/list_movies.json?query_term={quote(query)}&limit=1"
            response = self.session.get(search_url)
            if response.status_code == 200:
                data = response.json()
                movies = data.get("data", {}).get("movies", [])
                if movies:
                    movie_id = movies[0]["id"]
                    subtitle_url = f"https://yts.mx/api/v2/movie_details.json?movie_id={movie_id}&with_images=false"
                    response = self.session.get(subtitle_url)
                    if response.status_code == 200:
                        data = response.json()
                        movie = data.get("data", {}).get("movie", {})
                        subtitles = movie.get("subtitles", [])
                        for sub in subtitles:
                            if sub.get("lang") == "english":
                                return sub.get("url")
            return None
        except Exception as e:
            print(f"Error searching YIFY subtitles: {e}")
            return None

    def download_srt_from_url(self, url):
        try:
            if not url:
                return None
            response = self.session.get(url)
            if response.status_code == 200:
                content = response.text
                if content and ("1\n00:00:" in content or "WEBVTT" in content):
                    return content
                if "application/zip" in response.headers.get("Content-Type", ""):
                    print("ZIP file detected, trying alternative source...")
                    return None
                return content
            return None
        except Exception as e:
            print(f"Error downloading SRT: {e}")
            return None

    def download_subtitles(self, query):
        print(f"Searching for subtitles: {query}")
        print("Trying OpenSubtitles.org...")
        sub_info = self.search_opensubtitles(query)
        if sub_info:
            content = self.download_from_opensubtitles(sub_info)
            if content:
                return content, "OpenSubtitles.org"
        print("Trying YIFY subtitles...")
        sub_url = self.search_yify_subtitles(query)
        if sub_url:
            content = self.download_srt_from_url(sub_url)
            if content:
                return content, "YIFY Subtitles"
        return None, None

    def save_subtitle(self, content, filename):
        if not content:
            return False
        filename = re.sub(r"[^\w\s-]", "", filename)
        filename = re.sub(r"[-\s]+", "_", filename)
        if not filename.endswith(".srt"):
            filename += ".srt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Subtitle saved to: {filename}")
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False


def main():
    if len(sys.argv) < 2:
        print('Usage: python get_sub.py "movie_or_series_name"')
        print("Example: python get_sub.py outcast_s01")
        print('Example: python get_sub.py "The Witcher season 2"')
        sys.exit(1)
    query = " ".join(sys.argv[1:])
    downloader = SubtitleDownloader()
    content, source = downloader.download_subtitles(query)
    if content:
        print(f"✅ Subtitles found from {source}")
        filename = query.replace(" ", "_").replace(".", "_")
        downloader.save_subtitle(content, filename)
    else:
        print("❌ No subtitles found for the given query")
        print("Tips:")
        print("  - Try using the exact movie/TV show name")
        print("  - For TV series, use format: 'show_name_season_episode'")
        print("  - Example: 'breaking_bad_s01e01'")
        print("  - Try removing special characters")


if __name__ == "__main__":
    raise SystemExit(main())
