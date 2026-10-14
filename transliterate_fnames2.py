#!/data/data/com.termux/files/usr/bin/python
"""Write a Python command-line tool that converts Persian (Farsi) and Arabic-script file names into clean, portable ASCII file names. The tool should take a target directory as input, along with an option to choose whether to process only the top level or search subfolders recursively, and an option to preview changes without applying them (dry-run mode).
For each file and folder whose name contains Persian or Arabic-script characters, the tool should produce a romanized, Latin-alphabet equivalent using a sensible transliteration scheme. The transliteration should handle Persian and Arabic letters, Persian and Arabic-Indic digits (converting them to standard Western digits), diacritical marks (which should be removed), zero-width joiners and non-joiners (which should be handled appropriately, such as turning spaces or half-spaces into underscores), and common ligatures. Any remaining characters that are not letters, digits, dots, underscores, or hyphens should be replaced with underscores, and consecutive underscores should be collapsed into one. Leading and trailing underscores, dots, and hyphens should be trimmed. File extensions should be preserved in their original form.
The tool should apply Unicode normalization before transliteration so that visually identical characters are treated consistently. It must never overwrite an existing file: if a target name already exists, it should append a numeric suffix to create a unique name. Names that would become empty after cleaning should fall back to a sensible default. Renaming of folders must occur after the contents within them have been processed, so paths remain valid during the operation.
The tool should print a clear, human-readable report showing each planned or completed rename (original name and new name), a count of successful renames, and any errors encountered, such as permission problems, without stopping the entire run for a single failure. It should exit with a non-zero status code if any errors occurred and zero otherwise. Provide helpful command-line help text describing all options.
---"""

from __future__ import annotations
import argparse
import pathlib
import re
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
