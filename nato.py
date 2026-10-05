#!/data/data/com.termux/files/usr/bin/python3.12
"""Replace letters with NATO phonetic alphabet words."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

NATO = {
    "A": "Alpha",
    "B": "Bravo",
    "C": "Charlie",
    "D": "Delta",
    "E": "Echo",
    "F": "Foxtrot",
    "G": "Golf",
    "H": "Hotel",
    "I": "India",
    "J": "Juliett",
    "K": "Kilo",
    "L": "Lima",
    "M": "Mike",
    "N": "November",
    "O": "Oscar",
    "P": "Papa",
    "Q": "Quebec",
    "R": "Romeo",
    "S": "Sierra",
    "T": "Tango",
    "U": "Uniform",
    "V": "Victor",
    "W": "Whiskey",
    "X": "X-ray",
    "Y": "Yankee",
    "Z": "Zulu",
}


def to_nato(text: str) -> str:
    words = [NATO[ch.upper()] for ch in text if ch.isalpha() and ch.upper() in NATO]
    return " ".join(words)


def main() -> int:
    parser = argparse.ArgumentParser(description="Replace letters with NATO phonetic alphabet words.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("text", nargs="?", help="text to convert")
    group.add_argument("-f", "--file", type=Path, help="file to read text from")
    args = parser.parse_args()
    if args.file is not None:
        try:
            content = args.file.read_text(encoding="utf-8")
        except OSError as e:
            print(f"Error reading {args.file}: {e}", file=sys.stderr)
            return 1
    else:
        content = args.text
    print(to_nato(content))
    return 0


if __name__ == "__main__":
    sys.exit(main())
