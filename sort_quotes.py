#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that takes a JSON file path as its first argument, containing a list of quote objects each with "quote" and "author" fields.
The script should load the file, remove duplicate quotes (case-insensitive, whitespace-trimmed comparison), sort the remaining entries alphabetically by author name (case-insensitive), and write the result back to the same file in pretty-printed JSON with UTF-8 characters preserved.
It should gracefully handle a missing file or invalid/empty JSON content by printing a descriptive error message instead of crashing, and print "Success: Sorted" upon successful completion."""

from __future__ import annotations

import json
import os
import sys


def dedup_quotes(quotes):
    seen = set()
    unique = []
    for q in quotes:
        key = q["quote"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    return unique


def sort_quotes_by_author(path):
    if not os.path.exists(path):
        print(f"Error: '{path}' could not be found.")
        return
    with open(path, "r", encoding="utf-8") as f:
        try:
            quotes = json.load(f)
        except json.JSONDecodeError:
            print("Error: 'quotes.json' is empty or contains invalid formatting.")
            return
    uniques = dedup_quotes(quotes)
    uniques.sort(key=lambda item: item.get("author", "").lower())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(uniques, f, indent=2, ensure_ascii=False)
    print("Success: Sorted")


if __name__ == "__main__":
    fn = sys.argv[1]
    sort_quotes_by_author(fn)
