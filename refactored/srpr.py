#!/usr/bin/env python3
"""srpr.py — run ``srp`` for every lower-case and upper-case letter.

Handy for cycling a service through the whole alphabet; the tool's output is
streamed to the terminal exactly as the original's ``runcmd`` helper did.
"""

from __future__ import annotations

import argparse
import string
import subprocess
import sys

from loguru import logger

__version__ = "1.0.0"


class SrpRunner:
    """Invoke the ``srp`` tool once per letter."""

    def __init__(self, binary: str = "srp", *, dry_run: bool = False) -> None:
        """Store the executable name and whether to skip execution."""
        self._binary = binary
        self._dry_run = dry_run

    @staticmethod
    def letters() -> list[str]:
        """Return the lower-case letters followed by the upper-case ones."""
        return list(string.ascii_lowercase) + list(string.ascii_uppercase)

    def run(self) -> int:
        """Run the tool for every letter and return a process exit code."""
        for char in self.letters():
            command = [self._binary, char]
            if self._dry_run:
                print(" ".join(command))
                continue
            try:
                subprocess.run(command, check=False)
            except FileNotFoundError:
                logger.error("{} is not installed or not on PATH", self._binary)
                return 1
        printed = not self._dry_run
        if self._dry_run:
            print("dry run, nothing executed")
        elif printed:
            print("done")
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``srpr.py``."""
    parser = argparse.ArgumentParser(
        prog="srpr.py",
        description="Run srp for every letter of the alphabet.",
    )
    parser.add_argument(
        "--binary", default="srp", help="executable to invoke (default: srp)"
    )
    parser.add_argument("--dry-run", action="store_true", help="print the commands only")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and run the tool for every letter."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    return SrpRunner(args.binary, dry_run=args.dry_run).run()


if __name__ == "__main__":
    raise SystemExit(main())
