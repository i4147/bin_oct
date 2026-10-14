#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a project directory tree and identifies which text files are written in a natural (human) language, then reports the detected language of each. The tool should run from the current working directory and recursively walk its contents while ignoring version-control folders, dependency and build directories, hidden directories, and common binary or media file types. It should only consider files that contain readable text, skipping any binary content.
Key behaviors:
- Read each candidate file and extract a meaningful text sample, ignoring very short fragments that would yield unreliable results.
- Detect the natural language of the text using a lightweight offline language identification model, and report only detections whose confidence meets a reasonable threshold.
- Handle unreadable files, encoding problems, and I/O errors gracefully without stopping the scan.
- Produce a clear, human-readable report listing each file with its detected language and confidence, plus a summary of how many files were found per language and how many were skipped or inconclusive.
- Use colored, visually distinct terminal output for headings, language labels, and warnings, with a sensible fallback when the output is not a terminal.
- Allow the user to optionally filter results by language or confidence and to limit the scan to a given path, while defaulting to the current directory.
- Exit with a meaningful status code and display concise usage information when invoked incorrectly.
The result should be a robust, self-contained command-line utility that can be run safely on arbitrary project folders.
---"""

from __future__ import annotations
import math
from pathlib import Path
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
