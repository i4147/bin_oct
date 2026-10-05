#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that reads a text file (given as a single command-line argument) containing one hex color code per line, validates and keeps only lines matching the 6-digit hex pattern (e.g., #a1b2c3), and sorts them by converting each to HSV (hue, saturation, value) using the colorsys module.
The script should then overwrite the same file with the sorted color codes, one per line, normalized to lowercase.
If the script is run without exactly one argument, it should print a usage message and exit with status code 1."""

from __future__ import annotations
import colorsys
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"^#([0-9a-fA-F]{6})$")


def hex_to_hsv(hex_color: str) -> tuple[float, float, float]:
    r = int(hex_color[1:3], 16) / 255
    g = int(hex_color[3:5], 16) / 255
    b = int(hex_color[5:7], 16) / 255
    return colorsys.rgb_to_hsv(r, g, b)


def sort_key(color: str) -> tuple[float, float, float]:
    h, s, v = hex_to_hsv(color)
    return h, s, v


def main(path: str) -> None:
    with Path(path).open(encoding="utf-8") as f:
        colors = [line.strip() for line in f if HEX_RE.match(line.strip())]
    colors.sort(key=sort_key)
    with Path(path).open("w", encoding="utf-8") as f:
        f.writelines(c.lower() + "\n" for c in colors)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: sort_colors.py colors.txt")
        sys.exit(1)
    main(sys.argv[1])
