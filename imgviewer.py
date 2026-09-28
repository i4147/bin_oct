#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line script that renders an image directly in the terminal using ANSI 256-color background escape codes.
The script should accept an image file path as a command-line argument, load it with PIL, resize it to a fixed height of 100 pixels while preserving aspect ratio (doubling width to compensate for character cell proportions), and print a grid of colored space characters approximating each pixel's RGB value.
It should include a helper function that maps RGB values to the nearest ANSI 256-color palette index, handling grayscale pixels as a special case, and exit gracefully with an error message if the specified image file cannot be found."""

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
