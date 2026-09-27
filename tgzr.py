#!/data/data/com.termux/files/home/.local/bin/python
"""
Create a .tar.gz archive of a directory and then delete the original contents.

The script resolves the given root directory (defaults to the current directory),
writes an archive named ``<root-name>.tar.gz`` next to it, then removes every
entry inside the root concurrently using a multiprocessing pool of 8 workers.
"""

from __future__ import annotations

import multiprocessing
import shutil
import tarfile
from collections.abc import Iterable
from pathlib import Path

_WORKERS: int = 8


def _remove_item(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def remove_items_fast(items: Iterable[Path]) -> None:
    item_list: list[Path] = list(items)
    if not item_list:
        return

    with multiprocessing.Pool(processes=_WORKERS) as pool:
        async_results = [pool.apply_async(_remove_item, (item,)) for item in item_list]
        for result in async_results:
            result.get()


def compress_and_cleanup(root: Path = Path()) -> None:
    root = root.resolve()
    archive_name: str = f"{root.name}.tar.gz"
    archive_path: Path = root.parent / archive_name

    print(f"Creating archive: {archive_path}")
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(root, arcname=root.name)

    print("Archive created. Removing original files...")
    items: list[Path] = [
        item for item in root.iterdir() if item.resolve() != archive_path
    ]
    remove_items_fast(items)
    print("Cleanup complete.")


if __name__ == "__main__":
    compress_and_cleanup()
