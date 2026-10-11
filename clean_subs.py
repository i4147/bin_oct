#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI co a Python command-line tool with the following specification:

Build a Termux-targeted Python 3 command-line script (shebang pointing to the Termux Python path at /data/data/com.termux/files/usr/bin/env python) named as a subtitle cleaner. Its purpose is to scan subtitle files and derive a normalized episode label from each filename, such as "E05", for renaming purposes.

Requirements:

**Dependencies and imports**
- Use `from __future__ import annotations` for modern type hint syntax.
- Use the standard library `argparse`, `re`, and `pathlib.Path`.
- Import a `colored` helper from a third-party or local module named `dh`. The helper is imported but not required for the core logic; keep the import in place.

**Constants**
- A set of recognized file extensions containing only ".srt" (compared case-insensitively).
- A leading-junk regex, case-insensitive, that matches at the start of a string a run of at least 6 characters composed of digits, whitespace, dots, or hyphens (used to strip leading numeric prefixes like "01. " or "1 - ").
- A list of two episode-detection regexes, case-insensitive:
  1. Matches the `S##E##` pattern (season/episode), capturing the two-digit episode number.
  2. Matches the `#x##` pattern (e.g., 1x05), capturing the two-digit episode number after the "x", with the season being 1 to 2 digits before it.
- A "trash" regex, case-insensitive, matching common release-group and source tags (e.g., HDTV, WEB-DL, WEBRIP, BLURAY, iMovie-DL, ELKA, PARISA, KILLERS, FUM, TURBO, FA), where separators between letters in WEB-DL/WEBRIP-style tokens may be a hyphen, dot, space, or nothing. The trash regex is defined but should be applied only if the implementation chooses to strip tags; it is not required for the episode output.

**Functions**
1. `extract_episode(name: str) -> str | None`: Iterate the episode patterns in order; on the first match, return the last capturing group (the episode digits as a string). Return None if no pattern matches.
2. `clean_name(fname: str) -> str | None`: Strip leading junk using the leading-junk regex, call `extract_episode` on the result, and return `"E"` followed by the episode zero-padded to two digits (e.g., "E05"). Return None if no episode is found.
3. `collect_files(path: Path, recursive: bool) -> list[Path]`: If recursive, return all paths under `path` (via rglob) whose suffix lowercased is in the video extension set. Otherwise, return only direct child regular files (not directories) of `path` with matching suffixes.

**main()**
- Build an argparse parser with a description "Subtitle cleaner".
- Add `-r/--recursive` (store_true) and `-w/--write` (store_true) flags.
- Parse arguments, then collect files from the current working directory (`Path()`) using the recursive flag.
- If no files are found, print "No subtitle files found" and return.
- Notable behavior: the script currently ends after the empty-check. A complete implementation should, for each collected file, compute `clean_name` on its filename; when `-w/--write` is set, rename the file to the cleaned name (keeping its original extension and directory) and skip files where no episode is detected; without `-w`, print a preview of the proposed rename (old name → new name) without modifying anything. Report files with no detected episode. Print the outcome of every operation.
- Preserve the original file's extension (e.g., ".srt") in the new name, and avoid overwriting an existing file: if the target exists, report a conflict and skip it.
- Handle errors (e.g., permission errors or OS errors during rename) by printing a message for that file and continuing with the rest.

**Execution**
- Entry point: run `main()` under the standard `if __name__ == "__main__":` guard.
- Intended to be run from the directory containing the subtitle files, e.g., `python script.py -r -w`.
- Output should be plain, concise console messages.

Deliver a single runnable Python file meeting the above, with type hints matching the signatures described.
---"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from dh import colored

VIDEO_EXTS = {".srt"}
LEADING_JUNK = re.compile(r"^\s*[\d\s\.-]{6,}", re.IGNORECASE)
EPISODE_PATTERNS = [
    re.compile(r"S\d{2}E(\d{2})", re.IGNORECASE),
    re.compile(r"(\d{1,2})x(\d{2})", re.IGNORECASE),
]
TRASH = re.compile(
    r"(HDTV|WEB[-\. ]?DL|WEBRIP|BLURAY|IMOVIE[-\. ]?DL|ELKA|PARISA|KILLERS|FUM|TURBO|FA)",
    re.IGNORECASE,
)


def extract_episode(name: str):
    for pat in EPISODE_PATTERNS:
        m = pat.search(name)
        if m:
            return m.group(m.lastindex)
    return None


def clean_name(fname: str) -> str | None:
    name = LEADING_JUNK.sub("", fname)
    ep = extract_episode(name)
    if not ep:
        return None
    return f"E{ep.zfill(2)}"


def collect_files(path: Path, recursive: bool) -> list[Path]:
    if recursive:
        return [p for p in path.rglob("*") if p.suffix.lower() in VIDEO_EXTS]
    return [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS]


def main() -> None:
    ap = argparse.ArgumentParser("Subtitle cleaner")
    ap.add_argument("-r", "--recursive", action="store_true")
    ap.add_argument("-w", "--write", action="store_true")
    args = ap.parse_args()
    files = collect_files(Path(), args.recursive)
    if not files:
        print("No subtitle files found")
        return
    print(colored("\nPreview:", "cyan", attrs=["bold"]))
    for f in files:
        new_core = clean_name(f.name)
        if not new_core:
            print(colored("SKIP:", "yellow"), f.name)
            continue
        new_name = new_core + f.suffix
        target = f.with_name(new_name)
        print(colored("OLD:", "red"), f.name, colored("-> NEW:", "green"), new_name)
        if args.write:
            if target.exists():
                print(colored("  EXISTS, skipped", "yellow"))
            else:
                f.rename(target)
    if not args.write:
        print(colored("\nDry-run only. Use -w to apply.", "yellow"))


if __name__ == "__main__":
    raise SystemExit(main())
