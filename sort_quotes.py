#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes the path to a JSON file containing a list of quote records (each record is an object with at least a "quote" text field and an "author" field) and cleans up the collection in place. The script should remove duplicate quotes, treating two entries as duplicates when their quote text matches regardless of letter case or surrounding whitespace, keeping only the first occurrence. It should then reorder the remaining entries alphabetically by author name, ignoring case, and save the result back to the same file as human-readable, indented JSON that preserves non-ASCII characters. The file path should be provided as a command-line argument. If the file does not exist, the script should print a clear error message and exit without modifying anything. If the file is empty or contains malformed JSON, it should print a clear error message explaining the problem and leave the file untouched. On success, it should print a short confirmation message indicating the file was sorted. Handle entries that lack an author field gracefully by treating their author as an empty string for sorting purposes.
---"""

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
