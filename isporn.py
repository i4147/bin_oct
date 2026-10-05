#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans the current working directory for image files (.jpg, .jpeg, .png, .webp) and classifies each one using the NudeDetector model from the nudenet library, printing the filename along with its predicted class and confidence score in cyan-colored output.
It should create three output folders named "safe", "sexy", and "porn" if they don't already exist, presumably for later sorting of the images.
Files whose paths contain the segments "porn", "nude", "safr", or "sexy" should be skipped during classification.
The script should use helper functions from a local "dh" module (cprint for colored printing, get_files for recursive file discovery filtered by extension, and mpf for multiprocessing/parallel execution) to process all discovered files concurrently."""

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
