#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory for image files (JPG, JPEG, PNG, and WebP) and classifies each one using a local nudity-detection model, reporting the result for each image. The script should set up three output folders named "safe", "sexy", and "porn" in the working directory if they do not already exist, and should skip any file whose path already includes one of those category folders or a few other reserved folder names ("nude" and "safr") so previously sorted or excluded images are not reprocessed. For every remaining image, the script should run the detector, determine the most likely category and its confidence score, and print a concise, color-highlighted status line showing the file name, the category, and the score. The script should process the files in a simple, reliable manner, handle the detector's output gracefully, and run as a standalone command-line tool that requires no arguments.
---"""

from __future__ import annotations
from pathlib import Path
from dh import cprint, get_files, mpf
from nudenet import NudeDetector

safe_path = Path("safe")
sexy_path = Path("sexy")
porn_path = Path("porn")
safe_path.mkdir(exist_ok=True)
sexy_path.mkdir(exist_ok=True)
porn_path.mkdir(exist_ok=True)


def check_porn(path: str):
    det = NudeDetector()
    return det.detect(path)


def process_file(path) -> None:
    path = Path(path)
    if "porn" in path.parts:
        return
    if "nude" in path.parts:
        return
    if "safr" in path.parts:
        return
    if "sexy" in path.parts:
        return
    result = check_porn(str(path))
    cprint(f"{path.name} is {result['class']} {result['score']}", "cyan")


if __name__ == "__main__":
    cwd = Path.cwd()
    files = get_files(cwd, ext=[".jpg", ".jpeg", ".png", ".webp"])
    mpf(process_file, files)
