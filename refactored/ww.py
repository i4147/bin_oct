#!/usr/bin/env python3
"""ww.py — pack the current project into a wheel with ``wheel pack``.

The command runs from the parent directory so the distribution name is taken
from the directory itself, and the wheel is written to ``/sdcard/whl`` as the
original did.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from loguru import logger

__version__ = "1.0.0"

DEFAULT_OUTPUT = Path("/sdcard/whl")


class WheelPacker:
    """Pack a project directory into a wheel."""

    def __init__(self, project: Path, output: Path, *, dry_run: bool = False) -> None:
        """Store the project directory, the output directory and the dry-run flag."""
        self._project = project
        self._output = output
        self._dry_run = dry_run

    def command(self) -> list[str]:
        """Return the ``wheel pack`` command line."""
        return ["wheel", "pack", str(self._project), "-d", str(self._output)]

    def run(self) -> int:
        """Run ``wheel pack`` and return a process exit code."""
        command = self.command()
        if self._dry_run:
            print(" ".join(command))
            return 0
        try:
            completed = subprocess.run(
                command,
                cwd=self._project.parent,
                check=False,
            )
        except FileNotFoundError:
            logger.error("the wheel package is not installed")
            return 1
        if completed.returncode != 0:
            logger.error("wheel pack exited with {}", completed.returncode)
            return 1
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``ww.py``."""
    parser = argparse.ArgumentParser(
        prog="ww.py",
        description="Pack a project into a wheel with 'wheel pack'.",
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="project directory to pack (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"directory that receives the wheel (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument("--dry-run", action="store_true", help="print the command only")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and pack the project."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    project = args.project.resolve()
    if not project.is_dir():
        logger.error("{} is not a directory", project)
        return 1
    return WheelPacker(project, args.output, dry_run=args.dry_run).run()


if __name__ == "__main__":
    raise SystemExit(main())
