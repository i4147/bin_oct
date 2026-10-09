#!/data/data/com.termux/files/usr/bin/python
import argparse
import sys
from pathlib import Path

import pymupdf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str)
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="png",
        choices=["png", "jpg"],
        dest="fmt",
    )
    return parser.parse_args()


def convert(input_file: str, fmt: str) -> None:
    input_path = Path(input_file)
    output_dir = input_path.with_suffix("")
    output_dir.mkdir(parents=True, exist_ok=True)
    alpha = fmt == "png"
    with pymupdf.open(input_path) as doc:
        for index, page in enumerate(doc, start=1):
            pixmap = page.get_pixmap(dpi=300, alpha=alpha)
            out_path = output_dir / f"{input_path.stem}_page_{index:04d}.{fmt}"
            if fmt == "jpg":
                pixmap.save(str(out_path), output="jpg", jpg_quality=90)
            else:
                pixmap.save(str(out_path), output="png")


def main() -> None:
    args = parse_args()
    convert(args.input, args.fmt)


if __name__ == "__main__":
    main()
