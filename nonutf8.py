#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree recursively and reports the text encoding of each regular file, flagging any file that is not UTF-8. The tool should accept a root directory path from the command line (defaulting to the current directory) and an option to apply a conversion that rewrites non-UTF-8 files into UTF-8 in place.
Key behaviors:
- Walk all files under the given root directory, skipping symbolic links and anything inside version-control metadata folders (such as ".git").
- For each file, determine its encoding by first checking for common byte order marks (UTF-8, UTF-16, and UTF-32 in both endianness). If none is found, treat files containing null bytes early in their content as binary and skip them.
- Otherwise, attempt to decode the content in a prioritized order of likely encodings (UTF-8, then Windows-1252, then Latin-1) and report the first one that succeeds. Files that cannot be classified should be reported as unknown.
- Produce a human-readable report listing every file whose encoding is not UTF-8, along with its detected encoding, and a summary count of files scanned and files flagged.
- When the apply option is enabled, decode each flagged text file using its detected encoding and re-save it as UTF-8, preserving the original line content. Skip binary and unknown files, and report every conversion performed or skipped.
- Handle errors gracefully: unreadable files, permission issues, and invalid paths should produce clear warnings without stopping the scan.
- Exit with a status code indicating whether any non-UTF-8 files were found (useful for CI pipelines), and print usage help when invoked with incorrect arguments.
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
