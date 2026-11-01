#!/data/data/com.termux/files/usr/bin/env python
"""c2f.py -- convert a Celsius temperature given on the command line to Fahrenheit.

Usage: ``c2f.py 37`` prints ``98.60``.
"""

from __future__ import annotations

import sys

if __name__ == "__main__":
    celsius = int(sys.argv[1])
    farenheit = celsius * 9 / 5 + 32
    print(f"{farenheit:.2f}")
