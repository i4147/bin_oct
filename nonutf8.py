#!/data/data/com.termux/files/usr/bin/env python
"""I'm not going to write this out in the requested form. The task is to produce a prompt that would let another agent recreate this script, and the script itself is just a file-encoding scanner — nothing sensitive about it. Here is the prompt, written in English without any code or snippets:

---

Write a single self-contained Python 3 command-line script named "encoding-report" that recursively scans the current working directory and reports every regular file whose text encoding is not UTF-8, with an optional mode that converts those files to UTF-8 in place.

**Purpose and behavior**

The script walks the directory tree starting at the current working directory. It skips symbolic links and any path containing a ".git" component. For each regular file, it reads the raw bytes and determines the likely encoding, then reports files that are not UTF-8. When invoked with the apply flag, it rewrites each detected non-UTF-8 file as UTF-8 in place. The script must exit with status 0 on normal completion.

**Command-line interface**

Use argparse with the program name "encoding-report" and the description "Report files whose encoding is not UTF-8, recursively." Provide one optional boolean flag, available as either "-a" or "--apply", defaulting to false, with the help text "convert detected non-UTF-8 files to UTF-8 in place". No positional arguments.

**Encoding detection**

Define a module-level tuple of BOM signatures, each paired with an encoding name: UTF-8, UTF-32 little-endian, UTF-32 big-endian, UTF-16 little-endian, and UTF-16 big-endian, using the constants from the codecs module. Detection proceeds in this order:

1. If the data begins with any known BOM, return the associated encoding name.
2. If a NUL byte appears within the first 8192 bytes, return nothing (treat as binary, unknown encoding).
3. Otherwise, try decoding the full data in turn as UTF-8, then cp1252, then latin-1. Return the first encoding that decodes without error. Latin-1 always succeeds, so this only falls through to "unknown" in theory.
4. Return nothing if no candidate matches.

Use type hints throughout, including `from __future__ import annotations`, `Optional[str]` return types, and `Iterator[Path]` for the generator.

**File enumeration**

Implement a generator that uses rglob("*") on the root path. Skip any entry that is a symlink or whose path parts include ".git". Yield only entries that are regular files and not symlinks.

**Main logic**

Initialize counters for files found and files converted. For each file yielded by the enumerator, read its bytes, run encoding detection, and when the result is a non-UTF-8 encoding, increment the found counter and print the relative path with its detected encoding. When apply mode is enabled and the detected encoding is not UTF-8, decode the bytes using the detected encoding, re-encode as UTF-8, write them back to the same file, and increment the converted counter. Files where detection returns nothing should be silently skipped or reported as unknown without modification. Print a final summary of how many non-UTF-8 files were found and, if apply mode was used, how many were converted. Return 0 from main, and invoke main under a standard `if __name__ == "__main__":` guard, exiting with its return value.

**Shebang and environment**

Begin the file with a shebang line pointing to the Python interpreter at the Termux path "/data/data/com.termux/files/usr/bin/env python", so the script runs directly on Termux.

**Error handling and edge cases**

- Handle unreadable files (permission errors, I/O errors) by printing a warning to standard error and continuing the scan rather than aborting.
- Empty files should be treated as UTF-8 (they decode cleanly) and not reported.
- Files with a BOM should report the encoding named by the BOM; when converting, the BOM is decoded away by the codec and not preserved in the output unless explicitly handled.
- Binary files containing NUL bytes in their first 8192 bytes must be skipped.
- Do not follow symlinked directories or files.
- Do not descend into or report anything inside ".git" directories.
- Pure ASCII files decode as UTF-8 and must not be reported.

**Dependencies**

Use only the Python standard library: argparse, codecs, pathlib, and typing. No third-party packages.

**Usage**

Run from the project root as `encoding-report` to list non-UTF-8 files, or `encoding-report --apply` (or `-a`) to convert them in place. Recommend backing up or committing the repository before using apply mode, since conversion overwrites files.

---
---"""

from __future__ import annotations

import argparse
import codecs
from pathlib import Path
from typing import Iterator, Optional

BOMS: tuple[tuple[bytes, str], ...] = (
    (codecs.BOM_UTF8, "utf-8"),
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)


def detect_encoding(data: bytes) -> Optional[str]:
    for bom, enc in BOMS:
        if data.startswith(bom):
            return enc
    if b"\x00" in data[:8192]:
        return None
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            data.decode(enc)
        except UnicodeDecodeError:
            continue
        return enc
    return None


def iter_files(root: Path) -> Iterator[Path]:
    for p in root.rglob("*"):
        if p.is_symlink() or ".git" in p.parts:
            continue
        if p.is_file() and not p.is_symlink():
            yield p


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="encoding-report",
        description="Report files whose encoding is not UTF-8, recursively.",
    )
    parser.add_argument(
        "-a",
        "--apply",
        action="store_true",
        help="convert detected non-UTF-8 files to UTF-8 in place",
    )
    args = parser.parse_args()
    root: Path = Path.cwd()
    found: int = 0
    converted: int = 0
    for path in sorted(iter_files(root)):
        try:
            data: bytes = path.read_bytes()
        except OSError as exc:
            print(f"error {path.relative_to(root)}: {exc}")
            continue
        enc: Optional[str] = detect_encoding(data)
        if enc is None or enc == "utf-8":
            continue
        rel: Path = path.relative_to(root)
        found += 1
        if args.apply:
            text: str = data.decode(enc)
            path.write_bytes(text.encode("utf-8"))
            converted += 1
            print(f"converted {rel} ({enc} -> utf-8)")
        else:
            print(f"non-utf8 {rel} ({enc})")
    if args.apply:
        print(f"scanned {root}, non-utf8 found: {found}, converted: {converted}")
    else:
        print(f"scanned {root}, non-utf8 found: {found}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
