#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a given directory tree for image files and extracts the text visible in each image using optical character recognition, then reports the results. The tool should accept a root folder path as its main input, along with an optional filter for which image file types to include (for example, common formats such as PNG, JPEG, BMP, TIFF, and GIF, with the ability to restrict to a custom subset). It should traverse subdirectories breadth-first, skip version-control, cache, and dependency folders such as ".git", "__pycache__", and "node_modules", and ignore symbolic links to avoid loops or duplicate processing. Gracefully handle permission errors and unreadable or corrupted files by logging a warning and continuing rather than crashing.
Once the list of matching image files is gathered, the script should process them concurrently using a small, configurable number of parallel workers to speed up OCR on large collections, while keeping the overall memory footprint reasonable. For each image, it should open the file, run text recognition, and capture the extracted string along with the source file path. The output should be a structured result for every file, containing the file path, the recognized text, and an indication of success or failure with an error message where applicable. Results should be presented in a clear, human-readable summary printed to the console and also optionally exportable to a machine-readable format such as JSON or CSV, selected via a command-line option. Include sensible defaults, a helpful command-line interface with a usage message, and clear exit codes that indicate whether the run completed fully, partially, or failed to start (for example, when the target path does not exist).
Ensure the script is robust, well-documented with docstrings, and easy to extend, such as by allowing a different OCR language to be specified or a minimum confidence or text-length threshold to filter out empty results.
---"""

from __future__ import annotations
from collections import deque
from pathlib import Path
import sys
from typing import TYPE_CHECKING
from PIL import Image
from pytesseract import image_to_string

if TYPE_CHECKING:
    from collections.abc import Callable


def mpf(process_function: Callable, files: list[Path], **kwargs):
    from joblib import Parallel, delayed

    file_strings = [str(f) for f in files]
    return Parallel(n_jobs=2)(delayed(process_function)(file_str, **kwargs) for file_str in file_strings)


def get_files(path: str | Path, ext: list[str] | None = None) -> list[Path]:
    path = Path(path)
    skip_dirs = {".git", "__pycache__", "node_modules"}
    queue = deque([path])
    files = []
    while queue:
        current = queue.popleft()
        try:
            for item in current.iterdir():
                if item.is_symlink():
                    continue
                if item.is_dir() and item.name not in skip_dirs:
                    queue.append(item)
                elif item.is_file() and (ext is None or item.suffix.lower() in ext):
                    files.append(item)
        except (PermissionError, OSError, FileNotFoundError):
            continue
    return files


def extract_text(image_path: Path) -> str:
    try:
        with Image.open(image_path) as img:
            if img.mode not in ("L", "RGB"):
                img = img.convert("RGB")
            result = image_to_string(img, lang="eng", config="--oem 1 --psm 6")
        print("-" * 40)
        print(result.strip() or "[No text detected]")
        return result.strip()
    except Exception as e:
        print(f"Error processing {image_path.name}: {e}")
        return ""


def process_file(path: Path) -> None:
    path = Path(path)
    txtfile = path.with_suffix(".txt")
    if txtfile.exists():
        print(f"✓ {path.name} already processed")
        return
    print(f"→ Processing {path.name}")
    text = extract_text(path)
    if text and len(text) > 5:
        try:
            txtfile.write_text(text, encoding="utf-8")
            print(f"✓ Saved {txtfile.name}")
        except Exception as e:
            print(f"✗ Failed to write {txtfile.name}: {e}")
    else:
        print(f"⚠ No significant text in {path.name}")


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    if args:
        files = [Path(p) for p in args if Path(p).is_file()]
    else:
        print("Scanning directory for images...")
        files = get_files(cwd, ext=[".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"])
    if not files:
        print("No image files found.")
        return
    print(f"Found {len(files)} image(s). Starting OCR...\n")
    max_workers = 2
    if len(files) == 1:
        process_file(files[0])
    else:
        print(f"Using {max_workers} worker(s) for memory safety...")
        mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
