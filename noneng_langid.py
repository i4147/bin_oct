#!/data/data/com.termux/files/usr/bin/env python
"""Write a prompt for an AI coding agent to generate a Termux-targeted Python 3.12 command-line script that scans the current working directory tree for non-English text lines in source/text files, using language detection to flag likely-English content with a confidence score.

The script should:

1. Use a shebang pointing to the Termux Python interpreter (`#!/data/data/com.termux/files/usr/bin/python3.12`).
2. Recursively walk all files starting from the current working directory (`Path.cwd()`), implemented via a generator function `walk_files(root)` that:
   - Skips common non-source directories: `.git`, `.hg`, `.svn`, `__pycache__` `.venv`, `venv`, `env`, `dist`, `build`.
   - Skips any directory whose name starts with a dot (hidden directories).
   - Skips files whose extension (case-insensitive) is in a defined skip list covering compiled/binary/media/archive formats (e.g., `.pyc`, `.pyo`, `.so`, `.dll`, `.dylib`, `.exe`, `.bin`, `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.pdf`, `.z`, `.rar`, `.mp3`, `.mp4`, ``).
   - Recurses into subdirectories and yields eligible file paths.
3. Implement a `decode_text(path)` function that:
   - Reads the file as bytes, returning `None` on any `OSError`.
   - Treats the file as binary (returns `None`) if a null byte (`\\x00`) is found in the first 4096 bytes.
   - Attempts to decode the bytes trying encodings in this order: `utf-8`, `utf-16`, `latin-1`, returning the first successful decode, or `None` if all fail.
4. Implement an `iter_lines(text)` generator that splits the text into lines, strips whitespace, and yields `(line_number, line)` pairs (1-indexed) only for lines with length >= a `MIN_LEN` constant (set to 12) and containing at least one alphabetic character.
5. Implement a `detect(text)` function that uses the `py3langid` library's `rank()` function to get ranked language pred determines whether the text should be flagged (e.g., by checking if the top-ranked language is not English, or computing/returning a confidence score), using a `MIN_CONF` constant (set to 0.65) as the confidence threshold. Handle the case where `rank()` returns no results.
6. Define module-level constants exactly as described: `ROOT` (current working directory), `SKIP_DIRS`, `SKIP_EXTS`, `MIN_LEN`, `MIN_CONF`, and ANSI color code constants for terminal output formatting: `RESET`, `BOLD`, `YELLOW`, `MAGENTA`.
7. The overall program (main logic, to be completed) should walk through all eligible files, decode them, extract qualifying lines, run language detection on each line (or accumulate text per file), and print out findings with the file path, line number, and the detected line highlighted/colored using the ANSI codes, so a user can quickly spot non-English (or low-confidence-English) text scattered across a codebase.

The purpose of the script is to help developers audit a codebase for stray non-English strings (e.g., comments, log messages, string literals left in another language) that may have been accidentally left in during development, using lightweight per-line language identification rather than full NLP processing. It should use only the standard library plus `py3langid` Android, no command Importys` as needed for anyatting andling logic.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/Pdbgp2LCf3zySUK9VnQi8k"""

from pathlib import Path
import math
import sys
import py3langid as langid

ROOT = Path.cwd()
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
}
SKIP_EXTS = {
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".dylib",
    ".exe",
    ".bin",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    ".mp3",
    ".mp4",
    ".mov",
    ".avi",
    ".ico",
}
MIN_LEN = 12
MIN_CONF = 0.65

RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"


def walk_files(root: Path):
    for path in root.iterdir():
        if path.is_dir():
            if path.name in SKIP_DIRS or path.name.startswith("."):
                continue
            yield from walk_files(path)
        elif path.is_file():
            if path.suffix.lower() in SKIP_EXTS:
                continue
            yield path


def decode_text(path: Path):
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:4096]:
        return None
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


def iter_lines(text: str):
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if len(line) >= MIN_LEN and any(ch.isalpha() for ch in line):
            yield lineno, line


def detect(text: str):
    results = langid.rank(text)
    if not results:
        return None, 0.0
    top_lang, top_score = results[0]
    if len(results) >= 2:
        second_score = results[1][1]
        try:
            conf = 1.0 / (1.0 + math.exp(second_score - top_score))
        except OverflowError:
            conf = 0.0
    else:
        conf = 1.0
    return top_lang, conf


def main():
    print(f"{BOLD}Scanning: {ROOT}{RESET}")
    for path in walk_files(ROOT):
        text = decode_text(path)
        if text is None:
            continue
        rel = path.relative_to(ROOT)
        for lineno, line in iter_lines(text):
            lang, conf = detect(line)
            if lang and lang != "en" and conf >= MIN_CONF:
                print(f"{YELLOW}{rel}:{lineno}{RESET} {MAGENTA}[{lang} {conf:.2f}]{RESET} {line}")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
