#!/usr/bin/env python3
"""mergecss.py — merge every ``*.css`` file of the current directory with cleancss.

Runs the external ``cleancss`` tool with duplicate rules removed and a single
``merged.css`` as the result. The tool's own output is streamed straight to the
terminal, which is how the original behaved.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from loguru import logger

__version__ = "1.0.0"

MERGED_NAME = "merged.css"
CLEANCSS_ARGS = ("-O2", "removeDuplicateRules:on")


class CssMerger:
    """Build ``merged.css`` from the stylesheets of one directory."""

    def __init__(self, directory: Path, *, dry_run: bool = False) -> None:
        """Store the working directory and whether to skip the merge."""
        self._directory = directory
        self._dry_run = dry_run

    def _command(self) -> list[str]:
        """Return the cleancss command line for this directory."""
        return ["cleancss", *CLEANCSS_ARGS, "*.css", "-o", MERGED_NAME]

    def run(self) -> int:
        """Run cleancss and return its exit status, or 1 when it is missing."""
        command = self._command()
        if self._dry_run:
            print(" ".join(command))
            return 0
        try:
            completed = subprocess.run(
                command,
                cwd=self._directory,
                check=False,
            )
        except FileNotFoundError:
            logger.error("cleancss is not installed or not on PATH")
            return 1
        if completed.returncode != 0:
            logger.error("cleancss exited with {}", completed.returncode)
            return 1
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``mergecss.py``."""
    parser = argparse.ArgumentParser(
        prog="mergecss.py",
        description="Merge the CSS files of a directory with cleancss.",
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path.cwd(),
        help="directory holding the stylesheets (default: current directory)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print the cleancss command only"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and merge the stylesheets."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    return CssMerger(args.directory, dry_run=args.dry_run).run()


if __name__ == "__main__":
    raise SystemExit(main())
