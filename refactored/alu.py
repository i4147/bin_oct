#!/usr/bin/env python3
"""alu.py — list the packages that have an upgrade available.

Wraps ``apt list --upgradable`` and forwards the tool's output unchanged.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from loguru import logger

__version__ = "1.0.0"


class UpgradableLister:
    """Run the package manager's upgrade listing."""

    def __init__(self, *, dry_run: bool = False) -> None:
        """Store whether the command should only be reported."""
        self._dry_run = dry_run

    def command(self) -> list[str]:
        """Return the ``apt list --upgradable`` command line."""
        return ["apt", "list", "--upgradable"]

    def run(self) -> int:
        """Run the command and return a process exit code."""
        command = self.command()
        if self._dry_run:
            print(" ".join(command))
            return 0
        try:
            completed = subprocess.run(command, check=False)
        except FileNotFoundError:
            logger.error("apt is not available on this system")
            return 1
        return completed.returncode


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``alu.py``."""
    parser = argparse.ArgumentParser(
        prog="alu.py",
        description="List the packages that have an upgrade available.",
    )
    parser.add_argument("--dry-run", action="store_true", help="print the command only")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and list the upgradable packages."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    return UpgradableLister(dry_run=args.dry_run).run()


if __name__ == "__main__":
    raise SystemExit(main())
