#!/usr/bin/env python3
"""pyhead.py — print the first kilobyte of a file.

Text files are decoded with ``errors="ignore"`` so stray bytes never abort the
dump; when even that fails the raw bytes are printed instead, which is what the
original fallback did.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

__version__ = "1.0.0"

HEAD_BYTES = 1024


class FileHeadPrinter:
    """Print the beginning of one file."""

    def __init__(self, path: Path | None, limit: int = HEAD_BYTES) -> None:
        """Store the file to read (``None`` for stdin) and how much to show."""
        self._path = path
        self._limit = limit

    def read(self) -> str:
        """Return the first *limit* characters or bytes of the input as text."""
        if self._path is None:
            return sys.stdin.read(self._limit)
        try:
            with self._path.open(encoding="utf-8", errors="ignore") as handle:
                return handle.read(self._limit)
        except UnicodeError:
            with self._path.open("rb") as handle:
                return handle.read(self._limit).decode("utf-8", errors="ignore")

    def run(self) -> int:
        """Print the head of the input and return a process exit code."""
        print(self.read())
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``pyhead.py``."""
    parser = argparse.ArgumentParser(
        prog="pyhead.py",
        description="Print the first kilobyte of a file ('-' reads standard input).",
    )
    parser.add_argument("path", type=Path, help="file to read, or '-' for stdin")
    parser.add_argument(
        "--bytes",
        type=int,
        default=HEAD_BYTES,
        help=f"how many characters to print (default: {HEAD_BYTES})",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and print the head of the file."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    is_stdin = str(args.path) == "-"
    try:
        return FileHeadPrinter(None if is_stdin else args.path, args.bytes).run()
    except OSError as exc:
        logger.error("cannot read {}: {}", args.path, exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
