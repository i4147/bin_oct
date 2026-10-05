#!/data/data/com.termux/files/usr/bin/python3.12
"""Create a Python 3.12 command-line script (intended to run under Termux on Android, using shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that cleans terminal/log text files by stripping ANequences and otherifacts, rewriting each file in place with the cleaned text.

Purpose and behavior:
- The script accepts one or more file paths as command-line arguments.
- For each file, it reads the full text content (UTF-8, replacing undecodable bytes instead of crashing), then produces a cleaned version, and writes the cleaned text back to the same file path (overwriting it), printing a confirmation line like `cleaned: <path>` for each successfully processed file.
- If a file cannot be read or written (e.g., OS-level errors such as missing file or permission issues), print an error message to stderr in the form `error: cannot read <path>: <exception>` or `error: cannot write <path>: <exception>`, and skip/continue without crashing the whole run; the per-file processing function should return a boolean success/failure indicator.

Cleaning logic (core functionality) must include:
1. Normalize Windows-style line endings `\\r\\n` to `\\n`.
2. Remove ANSI escape sequences using a compiled regular expression that covers: CSI sequences (`ESC [ ... final byte`), OSC sequences terminated by BEL or ST (`ESC ] ... (BEL|ESC\\\\)`), DCS/other string sequences starting with `ESC` followed by one of `P X ^ _` and terminated by `ESC\\\\`, and simple two-character escape sequences (`ESC` followed by a byte in ranges covering `@-Z` and `\\`, `-`, `_`).
3. Process remaining standalone carriage returns (`\\r`) per line to emulate real terminal overwrite behavior: split each line on `\\r`, and for each subsequent chunk, overlay it onto the accumulated rendered line starting from the beginning, so that a chunk overwrites the previously rendered characters it covers while leaving any leftover trailing characters from the previous render intact (similar to how a terminal cursor returning to column 0 and printing would visually overwrite the line). This must be done per line (split on `\\n`, process each line independently, then rejoin with `\\n`).
4. Process backspace characters (`\\x08`) to emulate deletion: repeatedly remove any non-newline character immediately followed by a backspace (collapsing "char + backspace" pairs), looping until no more such pairs remain, then also strip any remaining stray backspace characters that weren't preceded by a removable character.
5. Remove remaining non-printable/control characters using a regex matching control character ranges `\\x00-\\x08`, `\\x0B-\\x0C`, `\\x0E-\\x1F`, and `\\x7F` (i.e., excluding `\\n` and `\\t`/`\\x09`, `\\x0A`, `\\x0D` which were already handled, but stripping other control bytes).

Structure the code with clearly separated, reusable functions: one for handling carriage-return overwrite logic, one for handling backspace collapsing, one top-level `clean(text)` function that applies normalization and all the above transformations in order (CRLF normalization → ANSI stripping → carriage return handling → backspace handling → control character stripping) and returns the cleaned string, and a `clean_file(path)` function that wraps file I/O around `clean()` with error handling as described above.

The script should use `pathlib.Path` for file path handling, Python's `re` module with a verbose/commented regex for the ANSI escape pattern, and should be structured to be invoked as a standalone CLI tool (processing `sys.argv` file arguments), suitable for batch-cleaning multiple log files captured from terminal sessions that contain progress bars, spinners, color codes, or other escape-sequence noise, so that the resulting files contain clean, readable plain text.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/7e3hfj2XTJ6GyzBUjfdhto"""

from __future__ import annotations
import re
import sys
from pathlib import Path

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
