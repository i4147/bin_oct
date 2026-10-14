#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a block of plain text from a file (or standformats it so that no exceeds a fixed maximum length of 120 characters, while preserving the original sentences and their order. The script should split the text into sentences ending in a period or exclamation mark, then process each sentence: if a sentence is longer than the lim it into shorter segments at the most natural nearby points, preferring the last comma, semicolon, colon, or question mark that fits within the limit, and falling back to a hard break at the limit only when no such punctuation isulting segment should be stripped of surrounding whitespace and placed on its own line in the output. Empty fragments should be discarded. The reformatted text should be written to standard output or to an output file specified by the user, and the script should accept the input and output paths as command-line arguments, with sensible error messages if the input file is missing or unreadable. Design the script so that the line-length limit and the set of preferred break characters are easy to configure, and make sure the tool handles multi-paragraph input gracefully, treating each paragraph independently so that paragraph boundaries are kept intact.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys

MAX_LEN = 120
BREAK_PUNCTS = [",", ";", ":", "?"]


def split_sentences(text: str):
    pattern = re.compile(r"[^.!]+[.!]", re.MULTILINE | re.DOTALL)
    sentences = pattern.findall(text)
    return [s.strip() for s in sentences if s.strip()]


def break_long_sentence(sentence: str, max_len: int = MAX_LEN):
    parts = []
    while len(sentence) > max_len:
        break_pos = -1
        window = sentence[:max_len]
        for p in BREAK_PUNCTS:
            pos = window.rfind(p)
            break_pos = max(break_pos, pos)
        if break_pos < 0:
            break_pos = max_len
        parts.append(sentence[: break_pos + 1].strip())
        sentence = sentence[break_pos + 1 :].strip()
    if sentence:
        parts.append(sentence.strip())
    return parts


def restructure_paragraph(paragraph: str) -> str:
    sentences = split_sentences(paragraph)
    lines = []
    for s in sentences:
        lines.extend(break_long_sentence(s, MAX_LEN))
    return "\n".join(lines)


def restructure_file(path: Path) -> None:
    backup = path.with_suffix(path.suffix + ".bak")
    text = path.read_text(encoding="utf-8", errors="ignore")
    backup.write_text(text, encoding="utf-8")
    paragraphs = re.split(r"\n\s*\n", text.strip(), flags=re.MULTILINE)
    new_paragraphs = [restructure_paragraph(p) for p in paragraphs]
    new_text = "\n\n".join(new_paragraphs) + "\n"
    path.write_text(new_text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python restructure_text.py <filename>")
        sys.exit(1)
    file_arg = Path(sys.argv[1])
    if not file_arg.exists():
        print(f"Error: file '{file_arg}' does not exist.")
        sys.exit(1)
    restructure_file(file_arg)


if __name__ == "__main__":
    raise SystemExit(main())
