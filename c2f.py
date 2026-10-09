#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that converts a temperature from Celsius to Fahrenheit using the command line.
The script should accept a single command-line argument representing the temperature in Celsius as an integer, apply the standard conversion formula (F = C * 9/5 + 32), and print the resulting Fahrenheit value formatted to two decimal places.
Use sys.argv to read the input and ensure the code runs under the standard "if __name__ == '__main__'" entry point."""

from __future__ import annotations
from pathlib import Path
import sys


if __name__ == "__main__":
    celsius = int(sys.argv[1])
    farenheit = celsius * 9 / 5 + 32
    print(f"{farenheit:.2f}")
