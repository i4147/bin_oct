#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a plain text file from a path given as a command-line argument and reads its contents aloud using the device's text-to-speech system (intended for Android/Termux environments). The script should print a brief usage message and exit with an error if no file path is provided, and report a clear error and exit if the file does not exist. Because text-to-speech engines handle only limited input length per call, the script must split the file's content into sequential chunks of at most roughly 3000 characters each, preferring to break on line boundaries so that sentences and lines stay intact; any single line longer than the limit must be further split into pieces of the maximum size. Empty or whitespace-only lines should be ignored. Each chunk should be spoken in order, one after another, waiting for each to finish before starting the next, and any failure from the speech system should be surfaced as an error to the user. The script should be runnable from the command line as a simple tool with no interactive prompts.
---"""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys


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
