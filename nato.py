#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts text into the NATO phonetic alphabet. The tool should accept input either as a direct command-line text argument or read from a specified file (exactly one of these input methods must be provided). For each al, the script should output its corresponding NATO phonetic alphabet word (for example, A becomes Alpha, B becomes Bravo, and so on through Z as Zulu), ignoring digits, spaces, punctuation, and other non-letter characters. Letters should be matched case-insensitively. The converted words should be presented as a single space-separated line printed to standard output. If a file is given and cannot be read (for example, because it does not exist or cannot be opened), the script should report a clear error message and exit with a non-zero status code rather than crashing with a raw traceback. The script should include a helpful command-line interface with a short description and usage guidance for the user.
---"""

from __future__ import annotations
import argparse
from pathlib import Path
import sys

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
