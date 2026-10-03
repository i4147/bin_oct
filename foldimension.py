#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively scans a given root directory for image files (jpg, jpeg, png, gif, bmp, tiff, webp, ico), uses Pillow to read each image's pixel dimensions, and groups files by their (width, height) size.
It should then organize the images into subfolders named after their resolution (e.g., "1920x1080"), placing any dimension that only has a single matching file into an "other" folder instead, while moving/copying files and avoiding filename collisions by appending an incrementing counter to duplicate names.
The script should gracefully handle missing Pillow by printing an install instruction and exiting, and should print warnings for files that fail to open as images rather than crashing."""

from __future__ import annotations

import shutil
import sys
from collections import defaultdict
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: This script requires Pillow. Install it with: pip install Pillow")
    sys.exit(1)
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    ".ico",
}


def collect_images(root: Path):
    size_to_files = defaultdict(list)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        try:
            with Image.open(path) as img:
                width, height = img.size
            size_to_files[width, height].append(path)
        except Exception as e:
            print(f"Warning: Skipping {path} - {e}")
    return size_to_files


def unique_destination(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    counter = 1
    while True:
        new_dest = parent / f"{stem}_{counter}{suffix}"
        if not new_dest.exists():
            return new_dest
        counter += 1


def organize_images(root: Path, size_to_files: dict) -> None:
    for (width, height), files in size_to_files.items():
        if len(files) == 1:
            folder = "other"
        else:
            folder = f"{width}x{height}"
        folder_path = root / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        for src in files:
            dest = folder_path / src.name
            dest = unique_destination(dest)
            shutil.move(src, dest)
            print(f"Moved: {src} -> {dest}")


def main() -> None:
    root = Path.cwd()
    print(f"Scanning {root} for image files...")
    size_to_files = collect_images(root)
    total_files = sum(len(v) for v in size_to_files.values())
    if total_files == 0:
        print("No image files found.")
        return
    print(f"Found {total_files} image(s) in {len(size_to_files)} resolution group(s).")
    organize_images(root, size_to_files)
    print("Done.")


if __name__ == "__main__":
    raise SystemExit(main())
