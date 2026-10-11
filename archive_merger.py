#!/data/data/com.termux/files/usr/bin/python
"""Create a self-contained Python 3 script that archives a folder into a tar or tar.gz file, with an optional cleanup step that deletes the original contents, and a command-line interface to run it. Follow these specifications closely.

**Purpose and overall behavior**

The script packages a directory into a single archive file and can optionally remove the source directory afterward. It is intended to run under Termux on Android, so its shebang line should point to the Termux Python interpreter path (`/data/data/com.termux/files/usr/bin/python`). The file must begin with `from __future__ import annotations` so type hints like `Path | None` work on older Python versions.

**Dependencies**

Use only the standard library: `argparse`, `multiprocessing` (imported as `mp`), `pathlib.Path`, `shutil`, `sys`, and `tarfile`. No third-party packages.

**Required functions**

1. `compress_tar(folder: Path, output: Path | None = None, cleanup: bool = False) -> bool`
   - If `output` is not provided, default the output base name to the folder's parent directory plus the folder's name with a `.tar` extension.
   - Create an uncompressed tar archive using `shutil.make_archive`, passing the output path without extension, format `"tar"`, root directory set to the folder's parent, and base directory set to the folder's name so archive entries are stored relative to the folder name.
   - If `cleanup` is true and the folder is a directory, remove it recursively with `shutil.rmtree`, then print `Cleaned up: <folder>`.
   - Wrap the whole operation in a try/except that catches `Exception`, prints `Error compressing: <error>`, and returns `False`. On success return `True`.

2. `compress_tgz_parallel(folder: Path, num_workers: int = 8, cleanup: bool = True) -> bool`
   - Resolve the folder to an absolute path first.
   - Build the archive name as the folder name plus `.tar.gz`, placed in the folder's parent directory.
   - Print `Creating archive: <archive_path>`, then write a gzip-compressed tar using `tarfile.open` in `"w:gz"` mode, adding the folder with `arcname` set to the folder name.
   - If `cleanup` is true: print `Removing original files...`, build a list of the folder's immediate children excluding the archive file itself (compare resolved paths), pass that list along with `num_workers` to a helper named `_remove_items_fast`, then print `Cleanup complete.`
   - Wrap in try/except catching `Exception`, print `Error: <error>`, and return `False`. Return `True` on success.
   - **Note:** the helper `_remove_items_fast(items: list[Path], num_workers: int)` must also be implemented. It should delete the given files and directories in parallel using a `multiprocessing` pool of `num_workers` processes, where each worker removes a single item: calling `shutil.rmtree` for directories and `unlink` for files (ignore or handle missing items gracefully). Use `mp.Pool` with `imap_unordered` or `map`, and close and join the pool.

3. `main()` entry point
   - Use `argparse` with a required positional argument `folder` (path to the directory to compress).
   - Optional flags: `--format` with choices `tar` and `tgz` (default `tgz`); `--output` for a custom output path (only meaningful for `tar`); `--cleanup` as a boolean flag to delete the source after archiving; `--workers` as an integer defaulting to 8, used for parallel cleanup.
   - Validate that the folder path exists and is a directory. If not, print an error message to stderr and exit with status 1 using `sys.exit`.
   - Dispatch to `compress_tar` for the `tar` format (passing the output path and cleanup flag) or to `compress_tgz_parallel` for `tgz` (passing worker count and cleanup flag).
   - Exit with status 0 on success and 1 if the function returns `False`.

4. Guard the entry point with `if __name__ == "__main__":` and call `main()`. Because the script uses multiprocessing, ensure the main block is guarded so child processes do not re-execute top-level code.

**Edge cases and behavior notes**

- Paths should be handled with `pathlib`, converting string output paths to `Path` objects where needed.
- Cleanup for the tgz format should never delete the newly created archive, even if it sits inside the folder being compressed; filter it out by comparing resolved paths.
- Cleanup removes the folder's contents (its immediate children), not necessarily the folder itself, in the tgz path; the tar path removes the whole folder directory. Preserve this distinction.
- Errors during archiving should be reported with a message and return `False` rather than crashing with a traceback.
- Use consistent, readable naming and short docstrings or comments only where they add clarity.

**Output requirements**

Produce a single complete Python file containing the shebang, imports, all three functions plus the `_remove_items_fast` helper, and the guarded entry point. Keep the code idiomatic and consistent with the style of a small command-line utility.
---"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import shutil
import sys
import tarfile
from pathlib import Path


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
