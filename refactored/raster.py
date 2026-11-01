#!/usr/bin/env python3
"""raster.py — rename a compiled extension to the CPython 3.14 Android ABI name.

Termux builds tag extensions with the interpreter and platform ABIs
(``cpython-314-arm-linux-androideabi``); this helper gives an existing ``.so``
file that exact suffix so imports resolve.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

__version__ = "1.0.0"

ABI_TAG = ".cpython-314-arm-linux-androideabi.so"


class AbiSuffixRenamer:
    """Rename an extension module to the expected ABI-tagged file name."""

    def __init__(self, source: Path, stem: str, *, dry_run: bool = False) -> None:
        """Store the source file, the requested stem and the dry-run flag."""
        self._source = source
        self._stem = stem
        self._dry_run = dry_run

    def target(self) -> Path:
        """Return the ABI-tagged path next to the source file."""
        return self._source.with_name(self._stem + ABI_TAG)

    def run(self) -> int:
        """Rename the file and return a process exit code."""
        target = self.target()
        if target.exists():
            logger.error("{} already exists", target)
            return 1
        if self._dry_run:
            print(f"{self._source} -> {target}")
            return 0
        try:
            self._source.rename(target)
        except OSError as exc:
            logger.error("cannot rename {}: {}", self._source, exc)
            return 1
        print(f"{self._source} -> {target}")
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``raster.py``."""
    parser = argparse.ArgumentParser(
        prog="raster.py",
        description="Rename an extension module to the Android ABI-tagged name.",
    )
    parser.add_argument("path", type=Path, help="compiled extension to rename")
    parser.add_argument("stem", help="module name without the ABI suffix")
    parser.add_argument("--dry-run", action="store_true", help="report the rename only")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and rename the extension."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    return AbiSuffixRenamer(args.path, args.stem, dry_run=args.dry_run).run()


if __name__ == "__main__":
    raise SystemExit(main())
