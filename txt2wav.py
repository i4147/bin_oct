#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a plain-text file from a user-supplied file path and reads its contents aloud using the device's text-to-speech capability, designed to run in a Termux environment on Android.
The script should:
- Accept a path to a UTF-8 encoded text file as its input and fail with a clear, human-readable error message if the file does not exist.
- Read the full contents of the file and split it into manageable segments so that very long documents are spoken in sequential portions rather than as one oversized utterance. Segment boundaries should respect line and paragraph structure where possible, and any single line that exceeds the maximum segment size must still be broken up so that no segment is too long.
- Ignore empty or whitespace-only segments so that silence is not produced unnecessarily.
- Speak each segment in order, waiting for each one to finish before starting the next, so the narration flows continuously from beginning to end.
- Report a failure clearly if the text-to-speech system returns an error, rather than silently continuing.
- Provide a simple command-line interface where the file path is supplied as an argument, with brief usage guidance shown when the argument is missing.
- Keep the design simple, readable, and dependency-light, relying only on standard facilities and the device's existing speech command.
---"""

from __future__ import annotations
from pathlib import Path
import subprocess


def speak_text(text: str) -> None:
    subprocess.run(["termux-tts-speak", text], check=True)


def read_text_file(path: str) -> str:
    path = Path(path)
    if not path.exists():
        msg = "error: file not found"
        raise FileNotFoundError(msg)
    return path.read_text(encoding="utf-8")


def chunk_text(text: str, max_chars=3000):
    chunks = []
    current = ""
    for paragraph in text.splitlines():
        if len(current) + len(paragraph) + 1 > max_chars:
            if current:
                chunks.append(current.strip())
                current = paragraph
            else:
                chunks.append(paragraph[:max_chars])
                current = paragraph[max_chars:]
        else:
            current += paragraph + "\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


def text_file_to_speech(path: str) -> None:
    text = read_text_file(path)
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks, start=1):
        print(f"Speaking chunk {i}/{len(chunks)}...")
        speak_text(chunk)


if __name__ == "__main__":
    text_file_to_speech("/sdcard/Download/sample.txt")
