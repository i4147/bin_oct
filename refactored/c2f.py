#!/usr/bin/env python3
"""c2f.py — convert a Celsius temperature to Fahrenheit.

Accepts a whole-number Celsius value on the command line and prints the
Fahrenheit equivalent with two decimals, matching the original output.
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger

__version__ = "1.0.0"


class TemperatureConverter:
    """Convert between the Celsius, Fahrenheit and Kelvin scales."""

    @staticmethod
    def celsius_to_fahrenheit(celsius: float) -> float:
        """Return *celsius* expressed in degrees Fahrenheit."""
        return celsius * 9 / 5 + 32

    @staticmethod
    def fahrenheit_to_celsius(fahrenheit: float) -> float:
        """Return *fahrenheit* expressed in degrees Celsius."""
        return (fahrenheit - 32) * 5 / 9

    @classmethod
    def fahrenheit_to_kelvin(cls, fahrenheit: float) -> float:
        """Return *fahrenheit* expressed in kelvin."""
        return cls.fahrenheit_to_celsius(fahrenheit) + 273.15


def _celsius(value: str) -> int:
    """Parse a Celsius value from the command line."""
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an integer: {value!r}") from exc


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``c2f.py``."""
    parser = argparse.ArgumentParser(
        prog="c2f.py",
        description="Convert a Celsius temperature to Fahrenheit.",
    )
    parser.add_argument("celsius", type=_celsius, help="temperature in degrees Celsius")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and print the converted temperature."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    fahrenheit = TemperatureConverter.celsius_to_fahrenheit(args.celsius)
    print(f"{fahrenheit:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
