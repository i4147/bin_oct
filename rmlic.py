#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that removes license/copyright header blocks from a batch of text or source files.
It should load a license file (e.g.
"/sdcard/lic") and split its content into separate boilerplate patterns using runs of at least 3 blank lines as delimiters, then convert each pattern into a whitespace-tolerant, case-insensitive regex (escaping special characters while allowing flexible newline/whitespace matching) to strip matching blocks from each target file's content.
For each processed file it should compare file size before and after cleaning, only rewrite the file if content chang statusors using helper functions like cprint, fsz, gsz, and get_nobinary from a local "dh" module.
The script should be designed to process multiple files, using a worker count constant (NUM_WORKERS = 8) to support concurrent/parallel processing."""

import re
from pathlib import Path
from dh import cprint, fsz, get_nobinary, gsz

LIC_FILE = Path("/sdcard/lic")
MIN_BLANK_LINES = 3
NUM_WORKERS = 8


def load_patterns(lic_path: Path) -> list[str]:
    try:
        content = Path(lic_path).read_text(encoding="utf-8", errors="ignore")
        pattern_separator = "\\n(?:\\s*\\n){" + str(MIN_BLANK_LINES) + ",}"
        patterns = re.split(pattern_separator, content)
        patterns = [p.strip() for p in patterns if p.strip()]
        for pattern in patterns:
            pattern[:50].replace("\n", "\\n")
        return patterns
    except Exception as e:
        print(f"Error loading patterns from {lic_path}: {e}")
        return []


def escape_for_regex(text: str) -> str:
    escaped = re.escape(text)
    return escaped.replace("\\n", "\\s*\\n\\s*")


def remove_patterns_from_content(content: str, patterns: list[str]) -> str:
    cleaned = content
    for pattern in patterns:
        regex_pattern = escape_for_regex(pattern)
        cleaned = re.sub(regex_pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    return cleaned


def process_file(path: Path, patterns: list[str]) -> tuple:
    path = Path(path)
    path = Path(path)
    before = gsz(path)
    original_content = path.read_text(encoding="utf-8")
    cleaned_content = remove_patterns_from_content(original_content, patterns)
    if len(cleaned_content) != len(original_content):
        path.write_text(cleaned_content, encoding="utf-8")
        cprint(f"{path.name} updated", "green", end=" | ")
        ds = before - gsz(path)
        cprint(f"{fsz(ds)}")
        del before, ds, cleaned_content, original_content, path


def main() -> None:
    if not LIC_FILE.exists():
        print(f"Error: License file not found: {LIC_FILE}")
        return
    patterns = load_patterns(LIC_FILE)
    if not patterns:
        print("No patterns found. Exiting.")
        return
    print()
    cwd = Path.cwd()
    all_files = get_nobinary(cwd)
    if not all_files:
        print("No files to process.")
        return
    for f in all_files:
        process_file(f, patterns)


if __name__ == "__main__":
    raise SystemExit(main())
