#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that reads a text file specified as the first argument and reads it aloud on a Termux/Android device using the "termux-tts-speak" command-line tool.
Since text-to-speech engines typically have input length limits, the script should split the file's content into chunks of at most 3000 characters each, breaking along line boundaries where possible and only splitting mid-line if a single line exceeds the limit.
It should validate that the file path exists, print the total number of chunks detected, then sequentially speak each chunk via subprocess calls while printing progress messages showing the chunk index and character count.
Handle the missing-file and missing-argument cases by printing a usage message and exiting with a non-zero status."""

import subprocess
import sys
from pathlib import Path


def speak_text(text: str) -> None:
    subprocess.run(["termux-tts-speak", text], check=True)


def chunk_text(text: str, max_chars: int = 3000):
    lines = text.splitlines()
    chunks = []
    current = ""
    for line in lines:
        candidate = (current + "\n" + line).strip() if current else line.strip()
        if not candidate:
            continue
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            while len(line) > max_chars:
                chunks.append(line[:max_chars])
                line = line[max_chars:]
            current = line.strip()
    if current.strip():
        chunks.append(current)
    return chunks


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python tts_from_file.py /path/to/file.txt")
        sys.exit(1)
    path = sys.argv[1]
    path = Path(path)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)
    text = path.read_text(encoding="utf-8", errors="ignore")
    chunks = chunk_text(text)
    print(f"Loaded {path}. Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks, start=1):
        print(f"Speaking chunk {i}/{len(chunks)} (chars={len(chunk)})...")
        speak_text(chunk)


if __name__ == "__main__":
    raise SystemExit(main())
