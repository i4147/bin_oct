#!/data/data/com.termux/files/usr/bin/env python
"""Create a Python 3 command-line script (intended to run under Termux on Android, using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that renames files and/or directories by transliterating Persian/Arabic (and related Unicode, e.g. Persian/Arabic digits and diacritics) characters in their names into ASCII-safe equivalents, producing clean, filesystem-safe filenames.

Requirements and behavior:

1. **Transliteration mapping**: Define a dictionary (e.g. `PERSIAN_MAP`) that maps Persian/Arabic letters, digits, diacritical marks, and special characters (including zero-width non-joiner/joiner, Arabic diacritics like fatha/kasra/damma/shadda/tanwin, Persian/Arabic-Indic digits 0-9, and variant letter forms such as "ك"/"ک", "ي"/"ی", "ۀ", "ہ", "ے") to their closest ASCII Latin-letter phonetic equivalents (e.g. "ب"→"b", "ش"→"sh", "گ"→"g", "خ"→"kh", "ژ"→"zh", "غ"→"gh"). Include at least one multi-character key (e.g. the combination "لا"→"la") to demonstrate handling of multi-character sequences. Map whitespace to underscore, and map characters with no phonetic value (like hamza) to an empty string.

2. **Transliteration function**: Implement a `transliterate(text: str) -> str` function that:
   - Iterates through the input string character by character (supporting lookahead for multi-character keys in the map, checking longer sequences first before falling back to single characters).
   - Replaces each matched Persian/Arabic character or sequence using the mapping dictionary.
   - Passes through unmapped characters, applying Unicode normalization (e.g. NFKD decomposition and stripping combining marks/diacritics) to convert accented Latin or other Unicode characters into plain ASCII where possible.
   - Removes or replaces any remaining unsafe characters using a regex (e.g. `SAFE_CHARS` pattern matching anything not in `[A-Za-z0-9._-]`), and collapses multiple consecutive underscores into a single underscore (e.g. via a `MULTIPLE_UNDERSCORES` regex), trimming leading/trailing underscores or separators.
   - Returns a clean ASCII string suitable for use as a filename.

3. **Command-line interface**: Use `argparse` to accept:
   - One or more file/directory paths (or a target directory to scan) as positional arguments.
   - An option to recurse into subdirectories.
   - A dry-run / preview flag that shows what the new names would be without actually renaming.
   - Possibly an option to skip or confirm overwriting if a target filename already collides with an existing file.

4. **File system operations**: Using `pathlib`, the script should:
   - Walk through the specified paths (and subdirectories if recursion is enabled).
   - For each file/directory whose name contains non-ASCII (Persian/Arabic or other transliterable) characters, compute the new transliterated name while preserving the file extension.
   - Rename the file/directory in place (using `Path.rename`), handling name collisions gracefully (e.g. by appending a numeric suffix).
   - Print a log of each rename action (original name → new name), and report dry-run results without modifying the filesystem if that flag is set.

5. **Robustness**: Handle edge cases such as empty strings, names that are entirely non-transliterable, already-ASCII names (skip or leave unchanged), and ensure the script does not crash on permission errors or missing files, printing a clear error message instead.

The overall purpose of the script is to batch-rename Persian/Arabic-named files and folders into readable, portable ASCII-only filenames suitable for cross-platform compatibility and use in Unix-like environments such as Termux.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/VKLr6XKBfiKZuZPrnUu7XW"""

from __future__ import annotations
import argparse
import pathlib
from pathlib import Path
import re
import sys
import unicodedata


PERSIAN_MAP: dict[str, str] = {
    "ا": "a",
    "آ": "a",
    "أ": "a",
    "إ": "e",
    "ب": "b",
    "پ": "p",
    "ت": "t",
    "ث": "s",
    "ج": "j",
    "چ": "ch",
    "ح": "h",
    "خ": "kh",
    "د": "d",
    "ذ": "z",
    "ر": "r",
    "ز": "z",
    "ژ": "zh",
    "س": "s",
    "ش": "sh",
    "ص": "s",
    "ض": "z",
    "ط": "t",
    "ظ": "z",
    "ع": "a",
    "غ": "gh",
    "ف": "f",
    "ق": "gh",
    "ک": "k",
    "ك": "k",
    "گ": "g",
    "ل": "l",
    "م": "m",
    "ن": "n",
    "و": "v",
    "ه": "h",
    "ی": "y",
    "ي": "y",
    "ئ": "y",
    "ء": "",
    "ة": "h",
    "ؤ": "o",
    "لا": "la",
    "ۀ": "h",
    "ہ": "h",
    "ے": "y",
    "۰": "0",
    "۱": "1",
    "۲": "2",
    "۳": "3",
    "۴": "4",
    "۵": "5",
    "۶": "6",
    "۷": "7",
    "۸": "8",
    "۹": "9",
    "٠": "0",
    "١": "1",
    "٢": "2",
    "٣": "3",
    "٤": "4",
    "٥": "5",
    "٦": "6",
    "٧": "7",
    "٨": "8",
    "٩": "9",
    "\u064b": "",
    "\u064c": "",
    "\u064d": "",
    "\u064e": "",
    "\u064f": "",
    "\u0650": "",
    "\u0651": "",
    "\u0652": "",
    "\u0670": "",
    "\u200c": "_",
    "\u200d": "",
    " ": "_",
}
SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
MULTIPLE_UNDERSCORES = re.compile(r"_+")


def transliterate(text: str) -> str:
    result: list[str] = []
    i = 0
    while i < len(text):
        if text.startswith("لا", i):
            result.append("la")
            i += 2
            continue
        char = text[i]
        if char in PERSIAN_MAP:
            result.append(PERSIAN_MAP[char])
            i += 1
            continue

        if char.isascii() and (char.isalnum() or char in "._-"):
            result.append(char)
            i += 1
            continue

        normalized = unicodedata.normalize("NFKD", char)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        if ascii_text:
            result.append(ascii_text)
        else:
            result.append("_")
        i += 1
    name = "".join(result)
    name = SAFE_CHARS.sub("_", name)
    name = MULTIPLE_UNDERSCORES.sub("_", name)
    name = name.strip("._- ")
    return name or "file"


def unique_path(path: pathlib.Path, reserved: set[pathlib.Path]) -> pathlib.Path:
    if path not in reserved and not path.exists():
        return path
    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if candidate not in reserved and not candidate.exists():
            return candidate
        counter += 1


def collect_entries(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(
        root.rglob("*"),
        key=lambda path: len(path.parts),
        reverse=True,
    )


def rename_tree(root: pathlib.Path, dry_run: bool) -> None:
    entries = collect_entries(root)
    reserved: set[pathlib.Path] = set()
    for entry in entries:
        original_name = entry.name
        if entry.is_file():
            new_stem = transliterate(entry.stem)
            new_name = f"{new_stem}{entry.suffix}"
        else:
            new_name = transliterate(original_name)
        if new_name == original_name:
            continue
        destination = unique_path(
            entry.parent / new_name,
            reserved,
        )
        reserved.add(destination)
        print(f"{entry} -> {destination}")
        if dry_run:
            continue
        try:
            entry.rename(destination)
        except OSError as exc:
            print(f"FAILED: {entry}: {exc}")
            reserved.discard(destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recursively transliterate Persian filenames/directories.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=pathlib.Path,
        help="files/directories to process; defaults to current directory",
    )
    parser.add_argument(
        "-a",
        "--apply",
        action="store_true",
        help="actually rename files/directories; default is dry-run",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    roots = args.paths or [pathlib.Path()]
    for root in roots:
        root = root.expanduser()
        if not root.exists():
            print(f"NOT FOUND: {root}")
            continue
        if root.is_file():
            new_name = transliterate(root.stem) + root.suffix
            if new_name == root.name:
                continue
            destination = unique_path(root.parent / new_name, set())
            print(f"{root} -> {destination}")
            if args.apply:
                try:
                    root.rename(destination)
                except OSError as exc:
                    print(f"FAILED: {root}: {exc}")
        elif root.is_dir():
            rename_tree(root, dry_run=not args.apply)


if __name__ == "__main__":
    main()
