#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line utility script that converts image files (such as PNG or other formats supported by OpenCV/Pillow) into JPG format, flattening any transparency onto a white background.
It should accept one or more file or directory paths as input, using a helper "get_files" function to gather files to process, and skip files that are already JPG or unsupported.
For each convertible file, it should compare the file size before and after conversion, avoid overwriting existing JPG files by generating a unique output path when needed, and print colored console status messages summarizing the conversion (including size change).
The script should prefer OpenCV (with NumPy) for image decoding and alpha blending if available, falling back to Pillow otherwise."""

import sys
from pathlib import Path
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
                img_b = (
                    b.astype(float) * alpha + white_bg.astype(float) * (1 - alpha)
                ).astype(np.uint8)
                img_g = (
                    g.astype(float) * alpha + white_bg.astype(float) * (1 - alpha)
                ).astype(np.uint8)
                img_r = (
                    r.astype(float) * alpha + white_bg.astype(float) * (1 - alpha)
                ).astype(np.uint8)
                final_img = cv2.merge((img_b, img_g, img_r))
            else:
                final_img = img
            success = cv2.imwrite(
                str(output_path), final_img, [int(cv2.IMWRITE_JPEG_QUALITY), 95]
            )
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
    files = (
        [Path(f) for f in args]
        if args
        else get_files(cwd, ext=[".webp", ".bmp", ".jpeg", ".png", ".tiff", "PNG"])
    )
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)
    diffsize = before - gsz(cwd)
    cprint(f"space freed: {fsz(diffsize)}")


if __name__ == "__main__":
    raise SystemExit(main())
