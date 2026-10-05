#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that reads a JSON file of quotes located at /sdcard/data/quotes/quotes.json, where each entry contains a "quote" and an "author" field, and selects one entry at random to display in the terminal.
It should gracefully do nothing if the file is missing, contains invalid JSON, or is empty.
The output should be formatted with horizontal divider lines sized to the current terminal width, with the quote and author printed in colored, blinking ANSI text.
Wrap the logic in a display_random_quote function and run it when the script is executed directly."""

from __future__ import annotations
import json
import os
import random
from shutil import get_terminal_size

FILE_NAME = "/sdcard/data/quotes/quotes.json"


def display_random_quote():
    if not os.path.exists(FILE_NAME):
        return
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        try:
            quotes = json.load(f)
        except json.JSONDecodeError:
            return
    if not quotes:
        return
    selected = random.choice(quotes)
    quote_text = selected.get("quote", "No quote content.")
    author_text = selected.get("author", "Unknown Author")
    N = get_terminal_size()[0]
    print("\n" + "─" * N)
    print(f'\033[5;96m"{quote_text}"\033[0m')
    print(f"\033[5;94m  — {author_text}\033[0m")
    print("─" * N + "\n")


if __name__ == "__main__":
    display_random_quote()
