#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that loads a set of license-header text blocks from a fixed license file on an Android-style device, splits them into separate patterns wherever several consecutive blank lines appear, and then scans a batch of source files to strip every occurrence of those license blocks from their contents. The tool should be designed for bulk cleanup of copied license or boilerplate headers across a directory tree of source files.
Key requirements:
- **Input:** A license/boilerplate file containing one or more text blocks, where individual blocks are separated by a minimum run of blank lines. The tool should ignore empty blocks and tolerate encoding issues in the input file. A target directory or list of files containing the source code to be cleaned.
- **Pattern handling:** Each block must be matched literally, while being tolerant of varying whitespace and line-ending differences (blank lines or extra spaces between lines should not prevent a match). Matching must be safe against regex special characters in the license text.
- **Processing:** Remove every matched license block from each target file's content, applying all patterns in sequence. Process files in parallel using a moderate number of worker threads or processes to speed up large batches.
- **Output:** Write the cleaned content back to each file only when a change was actually made. Report to the console which files were modified, along with a concise summary of the total number of files scanned and modified. Print clear error messages if the license file cannot be read, and continue gracefully if an individual file fails.
- **Behavior:** The tool must be idempotent, so running it twice produces no further changes. It should skip binary files, avoid touching files it cannot read or write, and never delete content that does not match a license block.
- **Robustness:** Handle missing files, permission errors, and empty license files without crashing. Keep the script self-contained and readable, with a short configuration section at the top for the license file location, the blank-line threshold, and the worker count.
---"""

from __future__ import annotations
from pathlib import Path
import re
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
