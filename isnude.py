#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory for image files (JPEG, PNG, and WebP) and automatically detects images containing nudity, moving each flagged image into a dedicated subfolder named "nude" so it can be reviewed or separated from the rest.
The script should:
- Accept an optional command-line flag that enables downscaling of large images (larger than 800 pixels in either dimension) before analysis to speed up detection, while leaving smaller images untouched. Without the flag, analyze images at their original size.
- Process images concurrently across multiple files to make batch scanning efficient.
- Skip any files that already reside inside the "nude" folder so that previously moved images are not reprocessed.
- Create the "nude" folder in the working directory if it does not already exist.
- For each image, print the filename as progress feedback and print the detection result details for transparency.
- When an image is classified as nude, print a highlighted notification with its filename and move the file into the "nude" folder, preserving its original name.
- Handle images that cannot be read or analyzed gracefully, so that a single failing file does not stop the overall batch.
- Operate only on the files in the current directory tree and make no network requests or external API calls.
---"""

from __future__ import annotations
from pathlib import Path
import sys
import cv2
from dh import cprint, get_files, mpf
import nude

nude_path = Path("nude")
nude_path.mkdir(exist_ok=True)
RESIZE = "-r" in sys.argv


def check_nude(path: str) -> bool:
    img = cv2.imread(path)
    h, w = img.shape[:2]
    n = nude.Nude(path)
    if (h > 800 or w > 800) and RESIZE:
        n.resize(maxheight=800, maxwidth=800)
    n.parse()
    del img, h, w
    print(n)
    return bool(n.result)


def process_file(path) -> None:
    path = Path(path)
    if "nude" in path.parts:
        return
    print(f"{path.name}")
    if check_nude(str(path)):
        cprint(f"{path.name} is nude", "cyan")
        new_path = nude_path / path.name
        path.rename(new_path)


if __name__ == "__main__":
    cwd = Path.cwd()
    files = get_files(cwd, ext=[".jpg", ".jpeg", ".png", ".webp"])
    mpf(process_file, files)
