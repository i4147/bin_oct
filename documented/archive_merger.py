#!/data/data/com.termux/files/usr/bin/env python

"""archive_merger.py -- create ``tar``/``tgz`` archives and remove the originals.

Archiving and the follow-up cleanup are separate steps so an interrupted run
leaves the source files intact.
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import shutil
import tarfile
from pathlib import Path


def compress_tar(folder: Path, output: Path | None = None, cleanup: bool = False) -> bool:
    """Pack *folder* into an uncompressed *output* tar archive.

    When *cleanup* is true the source folder is removed afterwards. Return ``True`` on
    success.
    """
    try:
        if output is None:
            output = folder.parent / f"{folder.name}.tar"
        shutil.make_archive(str(output), "tar", folder.parent, folder.name)
        if cleanup:
            if folder.is_dir():
                shutil.rmtree(folder)
            print(f"Cleaned up: {folder}")
        return True
    except Exception as e:
        print(f"Error compressing: {e}")
        return False


def compress_tgz_parallel(folder: Path, num_workers: int = 8, cleanup: bool = True) -> bool:
    """Pack the contents of *folder* into a gzipped tar beside it.

    Members are added sequentially but the optional cleanup runs on a process pool of
    *num_workers*. Return ``True`` on success.
    """
    try:
        folder = folder.resolve()
        archive_name = f"{folder.name}.tar.gz"
        archive_path = folder.parent / archive_name
        print(f"Creating archive: {archive_path}")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(folder, arcname=folder.name)
        if cleanup:
            print("Removing original files...")
            items = [item for item in folder.iterdir() if item.resolve() != archive_path]
            _remove_items_fast(items, num_workers)
            print("Cleanup complete.")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def _remove_item(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _remove_items_fast(items: list[Path], num_workers: int) -> None:
    if not items:
        return
    with mp.Pool(processes=num_workers) as pool:
        results = [pool.apply_async(_remove_item, (item,)) for item in items]
        for result in results:
            result.get()


def main() -> int:
    """Run the ``tar`` or ``tgz`` sub-command given on the command line.

    Return 0 on success and 1 when archiving fails.
    """
    parser = argparse.ArgumentParser(description="Archive creation and cleanup tool")
    subparsers = parser.add_subparsers(dest="mode", required=True)
    tar_parser = subparsers.add_parser("tar", help="Create TAR archive and optionally remove folder")
    tar_parser.add_argument("folder", type=Path, help="Folder to archive")
    tar_parser.add_argument("--output", type=Path, default=None, help="Output archive path")
    tar_parser.add_argument("--cleanup", action="store_true", default=False, help="Remove folder after compression")
    tgz_parser = subparsers.add_parser("tgz", help="Create TAR.GZ archive and cleanup contents")
    tgz_parser.add_argument("folder", type=Path, help="Folder to archive")
    tgz_parser.add_argument("--workers", type=int, default=8, help="Number of parallel workers")
    tgz_parser.add_argument("--no-cleanup", action="store_true", help="Keep original files")
    args = parser.parse_args()
    folder = Path(args.folder)
    if not folder.exists():
        print(f"Error: Folder '{folder}' not found.")
        return 1
    if not folder.is_dir():
        print(f"Error: '{folder}' is not a directory.")
        return 1
    if args.mode == "tar":
        success = compress_tar(folder, args.output, args.cleanup)
    elif args.mode == "tgz":
        success = compress_tgz_parallel(folder, args.workers, not args.no_cleanup)
    else:
        return 1
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
