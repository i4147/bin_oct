#!/data/data/com.termux/files/usr/bin/env python
"""svg2png.py -- render an SVG file to PNG with cairosvg."""

import sys
from pathlib import Path

import cairosvg


def main() -> int:
    """Render the SVG file named on the command line to a PNG beside it.

    With ``-r`` the SVG is deleted after a successful conversion.
    """
    svg = Path(sys.argv[1])
    png = svg.with_suffix(".png")

    cairosvg.svg2png(url=str(svg), write_to=str(png))
    print(f"Saved: {png}")

    if "-r" in sys.argv[2:]:
        svg.unlink()
        print(f"Removed: {svg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
