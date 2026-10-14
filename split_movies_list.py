#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a plain-text file provided as a command-line argument, where each non-empty line contains a web URL. Forate a path segment following the word "series" and extract it as a movie name, decoding any percent-encoded characters. Lines without a recognizable series segment should be skipped or reported without stopping the overall process. The script should collect the unique movie names it finds, sanitize them so they are safe to use as filenames on common operating systems (replacing forbidden characters, trimming stray spaces and dots, and falling back to a generic name if nothing remains), and handle these cases gracefully: display a usage message when no file argument is given, exit with a clear error when the input file does not exist, and tolerate malformed or blank lines. The final output should be a clean, deduplicated, sanitized list of movie names, printed to the console in a readable form, with a summary of how many URLs were processed and how many were recognized. Use UTF-8 encoding for reading the input and keep the behavior robust, predictable, and easy to follow for a user who runs it from the terminal.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys
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
