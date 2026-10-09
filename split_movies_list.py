#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that reads a text file of URLs (passed as the first argument) where each line contains a URL with a "series" segment followed by a movie name, and groups these URLs by that extracted movie name.
For each URL, it should decode and sanitize the movie name into a safe filename, skip and report lines with invalid or malformed URLs (missing the "series" segment), and write each group's URLs into a separate text file named after the movie inside a "split_movies" subdirectory created next to the input file.
The script should handle missing/invalid input file arguments by printing usage instructions and exiting with an error code.
"""

from __future__ import annotations
import re
import sys
from pathlib import Path
from urllib.parse import unquote


def safe_filename(name: str) -> str:
    name = unquote(name).strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    return name.strip(" .") or "unknown_movie"


def extract_movie_name(url: str) -> str | None:
    parts = url.split("/")
    try:
        series_index = parts.index("series")
        movie_name = parts[series_index + 1]
    except (ValueError, IndexError):
        return None
    return unquote(movie_name)


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: python {Path(sys.argv[0]).name} movies.txt")
        sys.exit(1)
    input_file = Path(sys.argv[1])
    if not input_file.is_file():
        print(f"Error: file not found: {input_file}")
        sys.exit(1)
    movies: dict[str, list[str]] = {}
    with input_file.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            url = line.strip()
            if not url:
                continue
            movie_name = extract_movie_name(url)
            if movie_name is None:
                print(f"Skipping invalid URL on line {line_number}: {url}")
                continue
            movies.setdefault(movie_name, []).append(url)
    output_directory = input_file.parent / "split_movies"
    output_directory.mkdir(exist_ok=True)
    for movie_name, urls in movies.items():
        output_file = output_directory / f"{safe_filename(movie_name)}.txt"
        with output_file.open("w", encoding="utf-8") as file:
            file.write("\n".join(urls))
            file.write("\n")
        print(f"Saved {len(urls)} URL(s) to {output_file}")
    print(f"\nFinished: {len(movies)} movie(s) processed.")


if __name__ == "__main__":
    main()
