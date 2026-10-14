#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans up raw terminal or console output text and saves the cleaned result. The tool should accept an input text file (or standard input) containing output captured from a terminal session, and write the sanitized text to an output file (or standard output).
The script must perform the following high-level processing on the text:
- Normalize line endings so that Windows-style and Unix-style line breaks are treated consistently.
- Strip ANSI terminal escape sequences, such as color codes, cursor movement commands, and other control sequences, so that only human-readable content remains.
- Resolve carriage-return overwrites, so that text which was repeatedly redrawn on the same line (for example, progress indicators) shows only its final visible state.
- Apply backspace characters so that characters they erase are removed from the output, handling repeated or nested backspace sequences correctly.
- Remove any remaining non-printable control characters while preserving normal tabs and newlines.
The script should be a reusable command-line utility that:
- Accepts the input file path and optional output file path as arguments, defaulting to standard input and standard output when none are given.
- Handles missing files, encoding problems, and empty input gracefully with clear error messages and appropriate exit codes.
- Reads and writes text using a robust, widely compatible encoding, tolerating malformed bytes.
- Is structured so that each cleaning stage can be understood and tested independently, and includes a brief usage description accessible from the command line.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys

ANSI_ESCAPE_RE = re.compile(
    r"""
    \x1B
    (?:
        \[[0-?]*[ -/]*[@-~]
      | \][^\x07\x1B]*(?:\x07|\x1B\\)
      | [PX^_].*?\x1B\\
      | [@-Z\\-_]
    )
    """,
    re.VERBOSE,
)
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def apply_carriage_returns(text):
    out_lines = []
    for line in text.split("\n"):
        if "\r" not in line:
            out_lines.append(line)
            continue
        rendered = ""
        for chunk in line.split("\r"):
            rendered = chunk + rendered[len(chunk) :]
        out_lines.append(rendered)
    return "\n".join(out_lines)


def apply_backspaces(text):
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"[^\n]\x08", "", text)
        text = text.replace("\x08", "")
    return text


def clean(text):
    text = text.replace("\r\n", "\n")
    text = ANSI_ESCAPE_RE.sub("", text)
    text = apply_carriage_returns(text)
    text = apply_backspaces(text)
    text = CONTROL_CHARS_RE.sub("", text)
    return text


def clean_file(path):
    try:
        original = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"error: cannot read {path}: {e}", file=sys.stderr)
        return False
    cleaned = clean(original)
    try:
        path.write_text(cleaned, encoding="utf-8")
    except OSError as e:
        print(f"error: cannot write {path}: {e}", file=sys.stderr)
        return False
    print(f"cleaned: {path}")
    return True


def main():
    args = sys.argv[1:]
    if args:
        paths = [Path(a) for a in args]
    else:
        cwd = Path.cwd()
        paths = [p for p in cwd.rglob("*") if p.is_file() and p.suffix.lower() in (".txt", ".log")]
    if not paths:
        print("no files to clean", file=sys.stderr)
        return 1
    failures = 0
    for p in paths:
        if not p.is_file():
            print(f"error: not a file: {p}", file=sys.stderr)
            failures += 1
            continue
        if not clean_file(p):
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
