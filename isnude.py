#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that scans the current working directory for image files (.jpg, .jpeg, .png, .webp) and uses the "nude" library to detect nudity in each one, optionally resizing images larger than 800x800 pixels before analysis when a "-r" command-line flag is passed.
For each detected image, it should load it with OpenCV to check its dimensions, run the nudity detection, print the result, and if nudity is detected, move the file into a "nude" subdirectory (created if it doesn't exist), skipping files already inside that subdirectory.
The script should process files concurrently using a multiprocessing/multithreading helper (mpf) and rely on shared utility functions (cprint, get_files, mpf) imported from a local "dh" module."""

from __future__ import annotations
import sys
from pathlib import Path
import cv2
import nude
from dh import cprint, get_files, mpf

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
