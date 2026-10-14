#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that displays an image directly in the terminal using colored block characters. The script should take a single image file path as a command-line argument. If no path is provided, it should print a brief usage message and exit gracefully.
When given a valid image, the script should open it, convert it to a standard color format, and scale it to fit the full width of the current terminal window while preserving the original aspect ratio. Because terminal character cells are taller than they are wide, the vertical scaling should be adjusted so the image does not appear stretched. The output should render two vertical pixels per character row using a half-block glyph, with the top pixel shown as the foreground color and the bottom pixel as the background color, using 24-bit ANSI true-color escape sequences. Each row of the rendered image should be followed by a reset of terminal styling so colors do not bleed into subsequent output.
The script should handle common image formats supported by a standard imaging library, and it should work with images of any size, including very small and very large files. Output should go straight to standard output so the result can be viewed immediately in any true-color-capable terminal. Keep the script self-contained, readable, and runnable as a standalone command-line tool.
---"""

from __future__ import annotations
from shutil import get_terminal_size
import sys
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
