#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line tool that scans a directory (optionally recursively) for image files—including PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF, and SVG (rendered via cairosvg if available)—and displays them directly in the terminal using Pillow for loading/conversion and a custom renderer that scales images to fit within given terminal width/height constraints (accounting for character cell aspect ratio by doubling the height in pixels).
It should accept command-line arguments via argparse for the target directory, recursion toggle, and max display dimensions, then iterate through discovered image paths and print each one to the console.
Include error handling for missing dependencies (like cairosvg for SVG support) and invalid or corrupted image files, using pathlib for filesystem operations and typing hints for clarity."""

import argparse
import io
import shutil
import sys
from pathlib import Path
from typing import Iterator
from PIL import Image
IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
    ".tiff",
    ".svg",
}
def load_image(file_path: Path) -> Image.Image:
    if file_path.suffix.lower() == ".svg":
        try:
            import cairosvg
            png_bytes = cairosvg.svg2png(url=str(file_path))
            return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        except ImportError:
            raise RuntimeError(
                "cairosvg is required to render SVG files. Run: pip install cairosvg"
            )
        except Exception as err:
            raise ValueError(f"Failed to render SVG file: {err}")
    img = Image.open(file_path)
    return img.convert("RGBA")
def find_images(target_dir: Path, recursive: bool = True) -> Iterator[Path]:
    if not recursive:
        for p in target_dir.iterdir():
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
                yield p
        return
    for root, _, files in target_dir.walk():
        for file in files:
            p = root / file
            if p.suffix.lower() in IMAGE_EXTENSIONS:
                yield p
def render_to_terminal(img: Image.Image, max_w: int, max_h: int) -> None:
    img_w, img_h = img.size
    if img_w == 0 or img_h == 0:
        return
    max_h_pixels = max_h * 2
    scale = min(max_w / img_w, max_h_pixels / img_h)
    new_w = max(1, int(img_w * scale))
    new_h_pixels = max(2, int(img_h * scale))
    if new_h_pixels % 2 != 0:
        new_h_pixels -= 1
    resized = img.resize((new_w, new_h_pixels), Image.Resampling.LANCZOS)
    pixels = resized.load()
    output = []
    for y in range(0, new_h_pixels, 2):
        row_str = []
        for x in range(new_w):
            r1, g1, b1, a1 = pixels[x, y]
            r2, g2, b2, a2 = pixels[x, y + 1]
            if a1 < 255:
                r1, g1, b1 = (
                    int(r1 * (a1 / 255)),
                    int(g1 * (a1 / 255)),
                    int(b1 * (a1 / 255)),
                )
            if a2 < 255:
                r2, g2, b2 = (
                    int(r2 * (a2 / 255)),
                    int(g2 * (a2 / 255)),
                    int(b2 * (a2 / 255)),
                )
            char = f"\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀\x1b[0m"
            row_str.append(char)
        output.append("".join(row_str))
    print("\n".join(output))
def main() -> None:
    parser = argparse.ArgumentParser(description="Terminal Image Viewer (timg clone)")
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        help="Files or directories to display (defaults to current dir recursively)",
    )
    parser.add_argument(
        "-W", "--width", type=int, default=None, help="Max terminal columns"
    )
    parser.add_argument(
        "-H", "--height", type=int, default=None, help="Max terminal rows"
    )
    args = parser.parse_args()
    term_columns, term_rows = shutil.get_terminal_size((80, 24))
    max_w = args.width or term_columns
    max_h = args.height or (term_rows - 2)
    targets: list[Path] = []
    if not args.inputs:
        targets = sorted(list(find_images(Path.cwd(), recursive=True)))
    else:
        for path in args.inputs:
            if path.is_dir():
                targets.extend(sorted(list(find_images(path, recursive=True))))
            elif path.is_file():
                targets.append(path)
    if not targets:
        print("No supported image files found.", file=sys.stderr)
        sys.exit(0)
    for file_path in targets:
        print(f"=== {file_path} ===")
        try:
            img = load_image(file_path)
            render_to_terminal(img, max_w, max_h)
        except Exception as e:
            print(f"[Error loading {file_path.name}: {e}]", file=sys.stderr)
        print()
if __name__ == "__main__":
    main()