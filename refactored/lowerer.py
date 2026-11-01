#!/usr/bin/env python3
"""lowerer.py — rewrite a text file in lower case.

The whole file is lower-cased in place; the write is atomic so an interrupted run
leaves the original intact.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

from reqs.atomicio import atomic_write

__version__ = "1.0.0"


class FileLowercaser:
    """Lower-case the contents of one text file."""

    def __init__(self, path: Path, *, dry_run: bool = False) -> None:
        """Store the target path and whether to skip the write."""
        self._path = path
        self._dry_run = dry_run

    def run(self) -> int:
        """Rewrite the file in lower case and return a process exit code."""
        content = self._path.read_text(encoding="utf-8")
        lowered = content.lower()
        if self._dry_run:
            print(f"would rewrite {self._path} ({len(content)} chars)")
            return 0
        atomic_write(self._path, lowered)
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``lowerer.py``."""
    parser = argparse.ArgumentParser(
        prog="lowerer.py",
        description="Rewrite a text file in lower case.",
    )
    parser.add_argument("path", type=Path, help="file to lower-case in place")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and lower-case the file."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    try:
        return FileLowercaser(args.path, dry_run=args.dry_run).run()
    except (OSError, UnicodeDecodeError) as exc:
        logger.error("cannot process {}: {}", args.path, exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
