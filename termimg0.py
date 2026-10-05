#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that renders an image directly in the terminal using ANSI truecolor escape codes.
The script should accept an image file path as a command-line argument, open it with Pillow, resize it to fit the current terminal width (auto-detected via shutil.get_terminal_size), and adjust the height to compensate for character aspect ratio.
It should iterate over pairs of pixel rows, using each pixel pair to set the background and foreground color of a half-block character (▀) so two vertically stacked pixels are displayed per printed character cell, resetting the color codes after each line.
If no image path is provided as an argument, it should print a usage message instead of running."""

from __future__ import annotations
import sys
from shutil import get_terminal_size
from PIL import Image


def print_image(image_path, width=40):
    img = Image.open(image_path).convert("RGB")
    aspect_ratio = img.height / img.width
    width = get_terminal_size()[0]
    height = int(width * aspect_ratio * 0.55)
    img = img.resize((width, height))
    pixels = img.load()
    for y in range(0, height - 1, 2):
        for x in range(width):
            r1, g1, b1 = pixels[x, y]
            r2, g2, b2 = pixels[x, y + 1]
            print(f"\033[48;2;{r1};{g1};{b1}m\033[38;2;{r2};{g2};{b2}m▀", end="")
        print("\033[0m")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python termimg.py <image_path>")
    else:
        print_image(sys.argv[1])
