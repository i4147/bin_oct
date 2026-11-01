#!/usr/bin/env python3
"""pathcmd.py — print the entries of ``PATH`` one per line.

Useful for spotting duplicate or missing directories in a Termux shell. The
environment is read inside :func:`main`, never at import time.
"""

from __future__ import annotations

import argparse
import os
import sys

from loguru import logger

__version__ = "1.0.0"


class PathEntryLister:
    """List the directories stored in a ``PATH``-style variable."""

    def __init__(self, variable: str = "PATH") -> None:
        """Store the name of the environment variable to read."""
        self._variable = variable

    def entries(self) -> list[str]:
        """Return the non-empty entries of the variable, in order."""
        raw = os.environ.get(self._variable, "")
        return [entry for entry in raw.split(os.pathsep) if entry]

    def run(self) -> int:
        """Print every entry and return a process exit code."""
        entries = self.entries()
        if not entries:
            logger.warning("{} is empty or unset", self._variable)
            return 1
        for entry in entries:
            print(entry)
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``pathcmd.py``."""
    parser = argparse.ArgumentParser(
        prog="pathcmd.py",
        description="Print the entries of a PATH-style environment variable.",
    )
    parser.add_argument(
        "--variable",
        default="PATH",
        help="environment variable to inspect (default: PATH)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and list the variable's entries."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    return PathEntryLister(args.variable).run()


if __name__ == "__main__":
    raise SystemExit(main())
