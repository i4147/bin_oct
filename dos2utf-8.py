#!/data/data/com.termux/files/usr/bin/env python
"""
Recursively apply dos2unix (CRLF/CR → LF) and convert non-binary files to UTF-8.
- Uses pathlib
- Parallel processing (ThreadPoolExecutor)
- Single read/write pass for both conversions
- Skips symlinks and common VCS/cache directories
- Binary detection via binaryornot
- Errors logged with loguru
- Fully type-annotated
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator

from dh import is_binary
from loguru import logger

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
)
# logger.add("dos2unix_utf8.log", rotation="10 MB", level="DEBUG")

# ---------------------------------------------------------------------------
# Directories to prune during traversal
# ---------------------------------------------------------------------------
SKIP_DIR_NAMES: set[str] = {
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    "node_modules",
    ".tox",
    "venv",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".cache",
    "dist",
    "build",
    ".eggs",
    ".idea",
    ".vscode",
}


def iter_files(root: Path) -> Iterator[Path]:
    """
    Yield regular files under *root*, pruning common skip directories
    and never following symlinks.
    """
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Prune directories in-place so os.walk does not descend into them
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not (Path(dirpath) / d).is_symlink()]

        for name in filenames:
            path = Path(dirpath) / name
            if path.is_symlink() or not path.is_file():
                continue
            yield path


def process_file(path: Path) -> None:
    """
    Read once → detect binary → normalize newlines → ensure UTF-8 → write once.
    """
    try:
        if is_binary(str(path)):
            return

        data = path.read_bytes()
    except OSError as exc:
        logger.error(f"Cannot read {path}: {exc}")
        return

    # Decode – prefer UTF-8, fall back to latin-1 (lossless for any byte sequence)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
        logger.debug(f"Fell back to latin-1 for {path}")

    # dos2unix
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    new_data = normalized.encode("utf-8")

    if new_data != data:
        try:
            path.write_bytes(new_data)
            logger.info(f"Converted → UTF-8 + LF: {path}")
        except OSError as exc:
            logger.error(f"Cannot write {path}: {exc}")


def main() -> None:
    root = Path.cwd()
    files = list(iter_files(root))

    if not files:
        logger.info("No eligible files found.")
        return

    logger.info(f"Processing {len(files)} files under {root} …")

    max_workers = min(32, len(files) or 1)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, f): f for f in files}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001
                path = futures[future]
                logger.error(f"Unexpected error on {path}: {exc}")

    logger.info("Done.")


if __name__ == "__main__":
    main()
