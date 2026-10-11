#!/data/data/com.termux/files/usr/bin/env python
"""Write a single, self-contained prompt that instructs an AI coding agent to build a Python command-line script with the following specification. Do not include code. The prompt must cover the script's purpose, inputs and outputs, dependencies, logic, error handling, edge cases, and usage.

---

Create a Python 3 command-line script (intended to run in a Termux environment on Android, so include a Termux-style shebang line pointing to the Termux Python binary) that organizes image files in a directory tree by their pixel dimensions.

**Purpose:** Recursively scan a root directory, identify image files by extension, read each image's width and height, and group files that share identical dimensions. For each group that contains more than one file, move the files into a new subdirectory named after that size (for example, `WIDTHxHEIGHT`). Groups with only one file should be left in place.

**Dependencies and startup:**
- Use the Pillow library (`PIL.Image`) to read image dimensions. Import it inside a try/except ImportError block; if missing, print the message `Error: This script requires Pillow. Install it with: pip install Pillow` and exit with status code 1.
- Use only the standard library otherwise: `shutil`, `sys`, `collections.defaultdict`, and `pathlib.Path`. Include `from __future__ import annotations` at the top.

**Recognized extensions (case-insensitive match on the file suffix):** `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`, `.ico`. Store these in a module-level set constant.

**Required functions:**

1. `collect_images(root: Path)` — Recursively iterate all entries under `root` using `rglob("*")`. Skip anything that is not a regular file, and skip files whose lowercased suffix is not in the extension set. For each remaining file, open it with Pillow inside a context manager, read `img.size` to get `(width, height)`, and append the path to a list in a `defaultdict(list)` keyed by the `(width, height)` tuple. If opening or reading a file raises any exception, print a warning in the form `Warning: Skipping <path> - <error>` and continue. Return the dictionary.

2. `unique_destination(dest: Path) -> Path` — If `dest` does not exist, return it unchanged. Otherwise, split it into stem, suffix, and parent, and try `parent / f"{stem}_{counter}{suffix}"` for counter = 1, 2, 3, … until a non-existent path is found; return that path.

3. `organize_images(root: Path, size_to_files: dict) -> None` — For each `(width, height)` group whose file list has length greater than 1, create a folder named `f"{width}x{height}"` directly under `root` (use `mkdir` with `parents=True` and `exist_ok=True`). For each file in the group, compute a destination inside that folder using its original filename, and call `unique_destination` to avoid overwriting. Move the file with `shutil.move`. Skip groups of size one. Consider a file that is already inside the target size folder — it should not cause an error; the move to the same location must be handled gracefully (for instance by checking whether the source already resides at the destination before moving).

**Main entry point (`main()` guarded by `if __name__ == "__main__":`):**
- Determine the root directory from the first command-line argument (`sys.argv[1]`). If no argument is provided, default to the current working directory.
- Convert it to a `Path`, and if it does not exist or is not a directory, print an informative error to stdout and exit with status 1.
- Call `collect_images`, then print the number of distinct sizes found and the total number of images scanned, then call `organize_images`, and print a completion message.
- Wrap the main workflow to handle a keyboard interrupt (Ctrl+C) gracefully, printing a brief cancellation message and exiting with a nonzero status, and handle other unexpected exceptions by printing an error message and exiting with status 1.

**Edge cases to honor:**
- Symbolic links and directories named like images must be ignored (only regular files are considered).
- Files with uppercase extensions must be recognized.
- Corrupt or non-image files with image extensions must be skipped with a warning, not crash the run.
- Name collisions in destination folders must be resolved by appending `_1`, `_2`, etc., before the extension.
- Files whose dimensions are unique are never moved.
- Traversal happens before any moves, so newly created size folders must not corrupt the scan (the scan is completed into memory first).

**Usage:** Run as `python script.py [directory]`. Output should be plain text progress messages to stdout. The script modifies the filesystem in place, so it should not perform any destructive deletion—only moves.

Produce the complete script as a single file, with docstrings or brief comments where helpful, and follow standard PEP 8 style.
---"""

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
