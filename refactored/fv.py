#!/usr/bin/env python3
"""fv.py — show a text file in a pager.

Undecodable bytes are replaced rather than raising, so binary-ish files still
display something useful. Use ``-`` to page standard input.
"""

from __future__ import annotations

import argparse
import pydoc
import sys
from pathlib import Path

from loguru import logger

__version__ = "1.0.0"


class FilePager:
    """Send the contents of one file to the system pager."""

    def __init__(self, path: Path | None) -> None:
        """Store the file to display; ``None`` means standard input."""
        self._path = path

    def read(self) -> str:
        """Return the text to display."""
        if self._path is None:
            return sys.stdin.read()
        return self._path.read_text(encoding="utf-8", errors="replace")

    def run(self) -> int:
        """Page the text and return a process exit code."""
        pydoc.pager(self.read())
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``fv.py``."""
    parser = argparse.ArgumentParser(
        prog="fv.py",
        description="Show a text file in a pager ('-' reads standard input).",
    )
    parser.add_argument("path", type=Path, help="file to display, or '-' for stdin")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and page the requested file."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    is_stdin = str(args.path) == "-"
    try:
        return FilePager(None if is_stdin else args.path).run()
    except OSError as exc:
        logger.error("cannot read {}: {}", args.path, exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
