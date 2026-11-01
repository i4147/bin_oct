#!/usr/bin/env python3
"""f2c.py — convert a Fahrenheit temperature to Celsius and kelvin.

Prints both scales on one line, keeping the original layout and spelling of the
labels (``celecius:`` and ``kelvin:``).
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger

__version__ = "1.0.0"


def _fahrenheit(value: str) -> int:
    """Parse a Fahrenheit value from the command line."""
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an integer: {value!r}") from exc


class FahrenheitReporter:
    """Print the Celsius and kelvin equivalents of one Fahrenheit value."""

    def __init__(self, fahrenheit: int) -> None:
        """Store the value to convert."""
        self._fahrenheit = fahrenheit

    def celsius(self) -> float:
        """Return the value expressed in degrees Celsius."""
        return (self._fahrenheit - 32) * 5 / 9

    def kelvin(self) -> float:
        """Return the value expressed in kelvin."""
        return self.celsius() + 273.15

    def run(self) -> int:
        """Print the converted scales and return a process exit code."""
        print(f"celecius: {self.celsius():.2f}  kelvin:{self.kelvin():.2f}")
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``f2c.py``."""
    parser = argparse.ArgumentParser(
        prog="f2c.py",
        description="Convert a Fahrenheit temperature to Celsius and kelvin.",
    )
    parser.add_argument("fahrenheit", type=_fahrenheit, help="temperature in degrees Fahrenheit")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and print the converted scales."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    return FahrenheitReporter(args.fahrenheit).run()


if __name__ == "__main__":
    raise SystemExit(main())
