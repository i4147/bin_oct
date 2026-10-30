#!/data/data/com.termux/files/usr/bin/env python
"""Example: dos2unix + UTF-8 conversion that also works inside archives."""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from binaryornot.check import is_binary
from loguru import logger

from archive_walker import AdvancedWalker, VirtualFile

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}")


def process_entry(entry: VirtualFile) -> None:
    try:
        # binaryornot needs a real path or we fall back to a simple NUL check
        data = entry.read_bytes()
        if b"\0" in data[:8192]:
            return
    except Exception as exc:
        logger.error(f"Cannot read {entry.path}: {exc}")
        return

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    new_data = normalized.encode("utf-8")

    if new_data != data:
        try:
            entry.write_bytes(new_data)
            logger.info(f"Converted → UTF-8 + LF: {entry.path}")
        except Exception as exc:
            logger.error(f"Cannot write {entry.path}: {exc}")


def main() -> None:
    with AdvancedWalker(".", max_archive_depth=3) as walker:
        # Collect first so we can optionally parallelise pure processing
        entries = list(walker)

        # Sequential is safest when writes must later rebuild archives.
        # If you only read, you can parallelise freely.
        for entry in entries:
            process_entry(entry)

    logger.info("Done (archives rewritten if any changes were made).")


if __name__ == "__main__":
    main()
