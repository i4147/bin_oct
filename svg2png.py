#!/data/data/com.termux/files/usr/bin/env python
import sys
from pathlib import Path

import cairosvg


def main() -> int:
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
