#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that displays an image in the terminal as colored block art, taking a single image file path from the command line. The script should load the image, report a clear error and exit gracefully if the file does not exist, and scale the image to a fixed display height of 100 character rows while preserving its original aspect ratio. Because terminal character cells are roughly twice as tall as they are wide, the output width should be doubled relative to the scaled width so the picture does not appear stretched. Each pixel of the resized image should be rendered as a single space character with its background colored using the 256-color ANSI terminal palette, mapping RGB values to the nearest palette entry (with a dedicated grayscale ramp for neutral tones and the 6×6×6 color cube for everything else). Each row should be printed on its own line, and every color block should be reset afterward so the terminal output stays clean. The script should run as a standalone command-line tool and produce no output beyond the rendered image.
---"""

from __future__ import annotations
import sys
import numpy as np
from PIL import Image


def get_ansi_color_code(r, g, b):
    if r == g and g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return round((r - 8) / 247 * 24) + 232
    return 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)


def get_color(r, g, b) -> str:
    return f"\x1b[48;5;{int(get_ansi_color_code(r, g, b))}m \x1b[0m"


def show_image(img_path: str) -> None:
    try:
        img = Image.open(img_path)
    except FileNotFoundError:
        sys.exit("Image not found.")
    h = 100
    w = int(img.width / img.height * h) * 2
    img = img.resize((w, h), Image.Resampling.LANCZOS)
    img_arr = np.asarray(img)
    for x in range(h):
        for y in range(w):
            pix = img_arr[x][y]
            print(get_color(pix[0], pix[1], pix[2]), end="")
        print()


if __name__ == "__main__":
    show_image(sys.argv[1])
