#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to recreate a Python command-line tool which scans the current directory tree for non-code natural-language text and detects its language, printing matches with colored highlighting. Requirements for the prompt:

You are building a single-file Python 3 command-line script for Termux (Android). Start the file with a shebang line pointing to the Termux Python interpreter at /data/data/com.termux/files/usr/bin/env python.

Purpose: Recursively scan the current working directory (resolved at startup as the root) for text files and identify lines of natural-language text, using language detection to flag lines that appear to be written in a language other than the expected one. Report each such line with its file path, line number, detected language, and confidence, and highlight the offending text in the output.

Dependencies: Use only the standard library (pathlib, math, sys) plus the third-party package py3langid, imported as langid. Use langid's language classification function to get a language code and probability for each candidate line. Do not require network access.

Configuration constants to define at module level:
- A set of directory names to skip during traversal: version control folders (.git, .hg, .svn), __pycache__, node_modules, virtual environment folders (.venv, venv, env), and build output folders (dist, build). Also skip any directory whose name starts with a dot.
- A set of file extensions to skip (case-insensitive): compiled Python bytecode, shared libraries and executables, binary blobs, common image formats (jpg, jpeg, png, gif, webp, ico), PDF, archives (zip, tar, gz, 7z, rar), and audio/video (mp3, mp4, mov, avi).
- MIN_LEN = 12: minimum character length a line must have to be analyzed.
- MIN_CONF = 0.65: minimum confidence threshold for reporting a detection.
- ANSI color constants for reset, bold, yellow, and magenta output.

Traversal: Implement a recursive generator that iterates directory contents, skips ignored directories and extensions, and yields only regular files. Skip symlinks-to-directories handling beyond what Path.is_dir/is_file provide.

File decoding: Read each file as bytes; if reading fails with an OSError, skip the file. If the first 4096 bytes contain a NUL byte, treat the file as binary and skip it. Otherwise try decoding in order: utf-8, utf-16, latin-1, returning the first successful decode, or None if all fail.

Line iteration: Split decoded text into lines with their 1-based line numbers. For each line, strip surrounding whitespace and skip lines shorter than MIN_LEN. Skip lines that look like code or non-prose (for example, lines consisting mostly of punctuation, symbols, or hex/identifier-like tokens, or lines containing typical code syntax); design a reasonable heuristic and document it in comments, keeping comment density modest and matching a simple, idiomatic style.

Detection: For each candidate line, call langid's classify to obtain a language code and probability. Report the line only when the detected language differs from the expected language and the probability is at least MIN_CONF. Define the expected language as a clearly named constant (default English, "en") that the agent should state at the top of the script.

Output: For each finding, print the relative path from ROOT, the line number, the detected language code and confidence (formatted as a percentage or two-decimal value), and the line text with the matched content highlighted using MAGENTA and BOLD ANSI codes, resetting with RESET. Use YELLOW for the header/path label. Print a final summary count of findings and files scanned. If no findings exist, print a clear message saying so.

Error handling and edge cases: Handle unreadable files, binary files, undecodable files, and empty files gracefully without crashing. Handle KeyboardInterrupt cleanly by printing a short message and exiting with status 130. Use sys.exit with a nonzero status when the root cannot be read. Be robust to files with mixed or odd line endings (use splitlines semantics). Avoid following the process of reading huge files into memory repeatedly; process one file at a time.

Execution: Provide a main() function guarded by if __name__ == "__main__": and call sys.exit with 0 when findings are absent and 1 when findings are present. Make the script executable with no required arguments; optionally accept no CLI arguments at all. Include brief module-level docstring explaining usage: run from the project directory, output lists suspicious non-English prose lines.

Deliver the complete, runnable single-file script with type hints on function signatures, consistent with the style of the description above.
---"""

import math
import sys
from pathlib import Path

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
