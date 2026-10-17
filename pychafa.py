#!/data/data/com.termux/files/usr/bin/python

from pathlib import Path
import shutil
import sys

from PIL import Image


def render_image(image_path: str | Path, max_width: int | None = None, max_height: int | None = None) -> None:
    """
    Renders an image in the terminal using 24-bit TrueColor ANSI escape codes
    and half-block characters.
    """
    path = Path(image_path)
    if not path.is_file():
        print(f"Error: File '{image_path}' not found.", file=sys.stderr)
        return

    try:
        img = Image.open(path).convert("RGBA")
    except Exception as e:
        print(f"Error opening image: {e}", file=sys.stderr)
        return

    # Get terminal dimensions
    term_cols, term_rows = shutil.get_terminal_size((80, 24))

    target_width = max_width or term_cols
    # Each text row displays 2 vertical pixels using half-blocks (▀)
    target_height = max_height or (term_rows * 2)

    # Calculate aspect ratio adjustment
    img_width, img_height = img.size
    aspect_ratio = img_height / img_width

    # Terminal character cells are roughly twice as tall as they are wide (~1:2 ratio).
    # Scaling height by 0.5 corrects this distortion.
    calc_height = int(target_width * aspect_ratio * 0.5) * 2

    if calc_height > target_height:
        calc_height = target_height & ~1  # Ensure even number for half-blocks
        calc_width = int((calc_height / 2) / (aspect_ratio * 0.5))
    else:
        calc_width = target_width
        calc_height = max(2, calc_height & ~1)

    # Resize image using high-quality resampling
    img = img.resize((calc_width, calc_height), Image.Resampling.LANCZOS)
    pixels = img.load()

    output: list[str] = []

    # Process image two vertical rows at a time
    for y in range(0, calc_height, 2):
        row_str = []
        for x in range(calc_width):
            r1, g1, b1, a1 = pixels[x, y]  # Top pixel
            r2, g2, b2, a2 = pixels[x, y + 1]  # Bottom pixel

            # Handle fully transparent pixels
            if a1 < 128 and a2 < 128:
                row_str.append(" ")
                continue

            # ANSI TrueColor escape sequences:
            # \x1b[38;2;R;G;Bm -> Foreground color (top pixel via upper half-block ▀)
            # \x1b[48;2;R;G;Bm -> Background color (bottom pixel)
            fg = f"\x1b[38;2{r1};{g1};{b1}m" if a1 >= 128 else "\x1b[39m"
            bg = f"\x1b[48;2;{r2};{g2};{b2}m" if a2 >= 128 else "\x1b[49m"

            row_str.append(f"{fg}{bg}▀")

        output.append("----" + "".join(row_str) + "\x1b[0m")  # Reset styling at end of line

    print("\n".join(output))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 chafa_clone.py <image_path>")
        sys.exit(1)
    render_image(sys.argv[1])
