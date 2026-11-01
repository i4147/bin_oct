#!/usr/bin/env python3
"""decode_unicode.py — fold a text file down to plain ASCII in place.

Compatibility forms are decomposed with ``unicodedata.normalize("NFKD")`` and
every remaining non-ASCII character is dropped, which turns accented and
full-width text into its unaccented ASCII spelling.
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

from loguru import logger

from reqs.atomicio import atomic_write

__version__ = "1.0.0"


class UnicodeAsciifier:
    """Reduce the contents of one text file to ASCII."""

    def __init__(self, path: Path, *, dry_run: bool = False) -> None:
        """Store the target path and whether to skip the write."""
        self._path = path
        self._dry_run = dry_run

    @staticmethod
    def asciify(text: str) -> str:
        """Return *text* with decomposed and non-ASCII characters removed."""
        return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

    def run(self) -> int:
        """Rewrite the file as ASCII and return a process exit code."""
        text = self._path.read_text(encoding="utf-8")
        result = self.asciify(text)
        if self._dry_run:
            print(f"would rewrite {self._path} ({len(text)} -> {len(result)} chars)")
            return 0
        atomic_write(self._path, result)
        print(f"{self._path} updated")
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``decode_unicode.py``."""
    parser = argparse.ArgumentParser(
        prog="decode_unicode.py",
        description="Rewrite a text file as plain ASCII.",
    )
    parser.add_argument("path", type=Path, help="file to rewrite in place")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and rewrite the file as ASCII."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    try:
        return UnicodeAsciifier(args.path, dry_run=args.dry_run).run()
    except (OSError, UnicodeDecodeError) as exc:
        logger.error("cannot process {}: {}", args.path, exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
