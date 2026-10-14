#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that analyzes a single image file provided as a command-line argument and reports whether the image is predominantly dark, predominantly bright, or mixed in tone. The script should accept the image path from the command line and, if no path is given, display a short usage message and exit with an error status.
The analysis should treat each pixel's perceived brightness as a weighted combination of its red, green, and blue channels, using a standard luminance weighting that reflects human visual sensitivity. A pixel counts as "dark" when its brightness falls below a fixed threshold (around 50 on a 0–255 scale). Compute the proportion of dark pixels across the whole image, then classify the image as:
- "Mostly Dark" if the dark-pixel proportion exceeds 60%,
- "Mostly Bright" if the dark-pixel proportion is below 40%,
- "Mixed" otherwise.
Both the dark-pixel threshold and the classification cutoff should be configurable through the function's parameters with those defaults. The script must handle images in any common format by converting them to a consistent RGB representation before analysis, and it should release the file properly after reading it.
Output should be two lines printed to the console:
1. The image's file name followed by the classification label (e.g., "photo.jpg: Mostly Dark").
2. The dark-pixel ratio, displayed as a value with two decimal places.
Note that the reported ratio is a fraction between 0 and 1, so ensure the displayed value is clearly and correctly formatted for the reader. Keep the implementation self-contained, readable, and suitable for running from a terminal on any operating system.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from PIL import Image


def analyze_image(path: Path, dark_threshold=50, ratio_threshold=0.6) -> tuple[str, float]:
    with Image.open(path) as img:
        img = img.convert("RGB")
        pixels = img.getdata()
        total = len(pixels)
        dark_count = 0
        for r, g, b in pixels:
            brightness = 0.299 * r + 0.587 * g + 0.114 * b
            if brightness < dark_threshold:
                dark_count += 1
        dark_ratio = dark_count / total
        if dark_ratio > ratio_threshold:
            return "Mostly Dark", dark_ratio
        if dark_ratio < 1 - ratio_threshold:
            return "Mostly Bright", dark_ratio
        return "Mixed", dark_ratio


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: script.py <image>")
        sys.exit(1)
    img_path = Path(sys.argv[1])
    result, ratio = analyze_image(img_path)
    print(f"{img_path.name}: {result}")
    print(f"Dark pixel ratio: {ratio:.2f}%")
