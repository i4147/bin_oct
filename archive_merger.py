#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that compresses a given folder into a tar archive, with optional compression and cleanup behaviors. The tool should accept a directory path from the command line, along with options to choose an output location, select an archive format (plain tar or gzip-compressed tar), control how many workers are used for compression, and decide whether the original folder should be deleted after a successful archive is created. It should validate that the input path exists and is a directory, resolve the archive name automatically from the folder name when no output path is given, and place the archive next to the source folder by default. The script should print clear progress messages indicating where the archive is being created and confirm when the original folder has been removed. Errors during compression should be caught, reported to the user in a readable way, and result in a non-zero exit status, with the original folder left intact whenever archiving fails. The overall design should be a small, self-contained command-line utility that is easy to run and reuse, and it should handle the case where the archive or target path already exists by informing the user or asking for confirmation before overwriting.
---"""

from __future__ import annotations
import argparse
import multiprocessing as mp
from pathlib import Path
import shutil
import tarfile


def compress_tar(folder: Path, output: Path | None = None, cleanup: bool = False) -> bool:
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
