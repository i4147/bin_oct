#!/data/data/com.termux/files/usr/bin/python
"""Negate images in place (the original files are overwritten).

Usage:
    python negate_inplace.py IMAGE [IMAGE ...]

Requires Pillow:  pip install pillow
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from dh import atomic_write

# Modes ImageOps.invert can handle directly (no channel juggling needed).
DIRECT_MODES = {"L", "RGB", "CMYK"}

# Metadata worth carrying over to the rewritten file.
META_KEYS = ("exif", "icc_profile", "dpi")


def negate(img: Image.Image) -> Image.Image:
    """Return a negated copy of *img*, preserving transparency if present."""
    if img.mode in DIRECT_MODES:
        return ImageOps.invert(img)

    has_alpha = "A" in img.getbands() or "transparency" in img.info
    if has_alpha:
        # Invert colour channels only, leave the alpha channel untouched.
        r, g, b, a = img.convert("RGBA").split()
        rgb = ImageOps.invert(Image.merge("RGB", (r, g, b)))
        r, g, b = rgb.split()
        return Image.merge("RGBA", (r, g, b, a))

    return ImageOps.invert(img.convert("RGB"))


def negate_inplace(path: Path) -> None:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    with Image.open(path) as img:
        img.load()
        fmt = img.format
        if not fmt:
            raise ValueError("unknown image format")
        meta = {k: img.info[k] for k in META_KEYS if k in img.info}
        out = negate(img)

    save_kwargs = dict(meta)
    if fmt == "JPEG":
        # Re-encoding a JPEG is inherently lossy; keep the damage minimal.
        save_kwargs["quality"] = 95

    # Encode to memory, then let dh.atomic_write handle the safe replacement.
    buf = io.BytesIO()
    out.save(buf, format=fmt, **save_kwargs)
    atomic_write(str(path), buf.getvalue())


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(f"usage: {Path(argv[0]).name} IMAGE [IMAGE ...]", file=sys.stderr)
        return 2

    rc = 0
    for arg in argv[1:]:
        p = Path(arg)
        try:
            negate_inplace(p)
            print(f"negated {p}")
        except (UnidentifiedImageError, FileNotFoundError, OSError, ValueError) as exc:
            print(f"error: {p}: {exc}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
