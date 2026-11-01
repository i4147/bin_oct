#!/usr/bin/env python3
"""cleanhistory.py — drop noise and duplicates from ``~/.bash_history``.

Removes the wrapper lines Termux writes for some shell escapes and keeps one
copy of every remaining command. Unlike the original, the surviving order is the
first-occurrence order rather than an arbitrary set order, so the file stays
stable across runs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

from reqs.atomicio import atomic_write

__version__ = "1.0.0"

NOISE_MARKER = 'cd "`printf'


class HistoryCleaner:
    """Clean one shell history file in place."""

    def __init__(self, path: Path, *, dry_run: bool = False) -> None:
        """Store the history path and whether to skip the write."""
        self._path = path
        self._dry_run = dry_run

    def clean(self, lines: list[str]) -> list[str]:
        """Return the lines without the noise marker and without duplicates."""
        kept = (line for line in lines if NOISE_MARKER not in line)
        return list(dict.fromkeys(kept))

    def run(self) -> int:
        """Rewrite the history file and return a process exit code."""
        if not self._path.is_file():
            logger.warning("{} does not exist, nothing to do", self._path)
            return 0
        with self._path.open(encoding="utf-8", errors="replace") as handle:
            cleaned = self.clean(handle.readlines())
        if self._dry_run:
            print(f"would keep {len(cleaned)} lines in {self._path}")
            return 0
        atomic_write(self._path, "".join(cleaned))
        print("done.")
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``cleanhistory.py``."""
    parser = argparse.ArgumentParser(
        prog="cleanhistory.py",
        description="Remove noise and duplicate commands from the shell history.",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.home() / ".bash_history",
        help="history file to clean (default: ~/.bash_history)",
    )
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and clean the history file."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    try:
        return HistoryCleaner(args.path, dry_run=args.dry_run).run()
    except OSError as exc:
        logger.error("cannot clean {}: {}", args.path, exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
