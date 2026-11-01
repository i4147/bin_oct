#!/usr/bin/env python3
"""empt.py — truncate a file to zero bytes.

The target is created when missing and emptied when it already exists. The write
goes through :mod:`reqs.atomicio`, so an interrupted run can never leave a
half-written file behind.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

from reqs.atomicio import atomic_write

__version__ = "1.0.0"


class FileEmptier:
    """Reduce a single file to zero bytes."""

    def __init__(self, path: Path, *, dry_run: bool = False) -> None:
        """Store the target path and whether to skip the write."""
        self._path = path
        self._dry_run = dry_run

    def run(self) -> int:
        """Empty the target file and return a process exit code."""
        if self._dry_run:
            print(f"would empty {self._path}")
            return 0
        atomic_write(self._path, "")
        print(f"{self._path} emptied")
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``empt.py``."""
    parser = argparse.ArgumentParser(
        prog="empt.py",
        description="Truncate a file to zero bytes.",
    )
    parser.add_argument("path", type=Path, help="file to empty")
    parser.add_argument(
        "--dry-run", action="store_true", help="report the target without writing"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and empty the requested file."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    try:
        return FileEmptier(args.path, dry_run=args.dry_run).run()
    except OSError as exc:
        logger.error("cannot empty {}: {}", args.path, exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
