#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that batch-converts image files to JPEG format. The script should accept a file or folder path as input, locate the image files to process, and produce a JPEG copy of each one alongside its original.
Key requirements:
- Accept one or more file paths or a directory from the command line; when a directory is given, process the images it contains.
- Skip anything that is not a regular file or is already a JPEG, printing a short notice for unsupported or invalid entries.
- Save each output next to the source file, reusing the original base name with a .jpg extension. If that name is already taken, generate a unique alternative rather than overwriting existing files.
- Handle images with transparency (alpha channel) by compositing them onto a solid white background so no transparent areas turn black or distorted.
- Support common input formats such as PNG, BMP, GIF, TIFF, and WebP, and convert color modes appropriately (e.g., grayscale, palette, or RGBA images) to RGB before saving.
- Use a reasonable JPEG quality setting that balances file size and visual fidelity.
- Report, for each file, the original size and the resulting size, along with a summary of how many files were converted, skipped, or failed.
- Gracefully report decoding or write errors for individual files without stopping the entire batch.
- Prefer a high-performance image library when available, but fall back to a more widely available imaging library if it is not installed, producing equivalent results either way.
- Provide clear console output so the user can follow progress and understand any problems.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import cprint, fsz, get_files, gsz, mpf, rrs, unique_path

try:
    import cv2
    import numpy as np

    USE_CV2 = True
except ImportError:
    from PIL import Image

    USE_CV2 = False


def process_file(path):
    path = Path(path)
    if not path.is_file():
        print(f"Skipping: {path.name} (Unsupported format or not a file)")
        return
    if path.suffix.lower() == ".jpg":
        return
    output_path = path.with_suffix(".jpg")
    if output_path.exists():
        output_path = unique_path(output_path)
    before = gsz(path)
    try:
        if USE_CV2:
            img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if img is None:
                print(f"Error: Could not decode {path.name}")
                return
            if img.shape[2] == 4:
                b, g, r, a = cv2.split(img)
                white_bg = np.full(img.shape[:2], 255, dtype=np.uint8)
                alpha = a.astype(float) / 255.0
                img_b = (b.astype(float) * alpha + white_bg.astype(float) * (1 - alpha)).astype(np.uint8)
                img_g = (g.astype(float) * alpha + white_bg.astype(float) * (1 - alpha)).astype(np.uint8)
                img_r = (r.astype(float) * alpha + white_bg.astype(float) * (1 - alpha)).astype(np.uint8)
                final_img = cv2.merge((img_b, img_g, img_r))
            else:
                final_img = img
            success = cv2.imwrite(str(output_path), final_img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        else:
            img = Image.open(path)
            if img.mode in {"RGBA", "LA"}:
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                final_img = background
            else:
                final_img = img
            final_img.save(output_path, "JPEG", quality=95)
            success = True
        if success:
            path.unlink()
            after = gsz(output_path)
            rrs(path, before, after)
            return
        return
    except Exception:
        return


def main() -> None:
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    files = [Path(f) for f in args] if args else get_files(cwd, ext=[".webp", ".bmp", ".jpeg", ".png", ".tiff", "PNG"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)
    diffsize = before - gsz(cwd)
    cprint(f"space freed: {fsz(diffsize)}")


if __name__ == "__main__":
    raise SystemExit(main())
