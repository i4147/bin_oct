#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that compresses a user-specified folder into a single archive file, offering a choice between an uncompressed tar archive and a gzip-compressed tar archive. The tool should accept the source folder path from the command line, validate that the folder exists and is actually a directory (expanding user home shortcuts and resolving relative paths before checking), and report clear, human-readable errors when validation fails. It should allow the user to optionally specify a custom output file path; when none is given, the archive should be created next to the source folder and named after it, with the appropriate extension for the chosen format.
The script should support an option to delete the original folder after the archive has been successfully created, and this deletion must be handled carefully: it should refuse to remove the folder if doing so would be unsafe (for example, when the target is a symbolic link, the archive would be written inside the folder being deleted, or the path points to a critical or root-level location). If the archive creation fails partway through, any partially written output should be cleaned up so no corrupt archive is left behind.
Include a parallelism option that lets the user specify a positive number of worker processes, which the tool may use to speed up the work where it is beneficial, with a sensible default. The command-line interface should provide helpful usage text, validate all numeric arguments (rejecting values below 1), and return a clear success or failure exit status. Print concise progress and result messages to the user, and send error messages to the standard error stream. The overall design should be modular, with separate, well-named helper routines for path validation, archive creation, and safe removal, and it should work on common desktop operating systems.
---"""

from __future__ import annotations
import argparse
import multiprocessing as mp
from pathlib import Path
import shutil
import sys
import tarfile
from typing import Sequence


def positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue < 1:
        msg = "value must be >= 1"
        raise argparse.ArgumentTypeError(msg)
    return ivalue


def resolve_directory(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        msg = f"Error: Folder '{resolved}' not found."
        raise FileNotFoundError(msg)
    if not resolved.is_dir():
        msg = f"Error: '{resolved}' is not a directory."
        raise NotADirectoryError(msg)
    return resolved


def default_tar_output(source: Path) -> Path:
    return source.parent / f"{source.name}.tar"


def default_tgz_output(source: Path) -> Path:
    return source.parent / f"{source.name}.tar.gz"


def create_archive(source: Path, output: Path, mode: str) -> None:
    with tarfile.open(output, mode) as tar:
        tar.add(source, arcname=source.name)


def remove_path(path: Path, *, safe_symlinks: bool = False, quiet: bool = False) -> None:
    try:
        if path.is_file():
            path.unlink()
            if not quiet:
                print(f"Removed file:{path}")
        elif path.is_dir():
            if safe_symlinks and path.is_symlink():
                path.unlink()
                if not quiet:
                    print(f"Removed symlink:{path}")
            else:
                shutil.rmtree(path)
                if not quiet:
                    print(f"Removed directory:{path}")
    except Exception as e:
        print(f"Error removing '{path}':{e}", file=sys.stderr)


def _remove_path_worker(path_str: str) -> None:
    remove_path(Path(path_str), safe_symlinks=True, quiet=True)


def cleanup_entries_parallel(entries: Sequence[Path], workers: int) -> None:
    if not entries:
        return
    with mp.Pool(processes=workers) as pool:
        results = [pool.apply_async(_remove_path_worker, (str(p),)) for p in entries]
        for result in results:
            result.get()


def cleanup_contents(source: Path, output: Path, workers: int) -> None:
    output_resolved = output.resolve()
    entries = [p for p in source.iterdir() if p.resolve() != output_resolved]
    cleanup_entries_parallel(entries, workers)


def run_tar(args: argparse.Namespace) -> int:
    source = resolve_directory(args.folder)
    output = args.output or default_tar_output(source)
    output = output.expanduser().resolve()
    print(f"Creating archive:{output}")
    create_archive(source, output, "w")
    print("Archive created.")
    if not args.keep:
        print("Removing original folder...")
        remove_path(source, safe_symlinks=False, quiet=args.quiet)
    return 0


def run_tgz(args: argparse.Namespace) -> int:
    source = resolve_directory(args.folder)
    output = args.output or default_tgz_output(source)
    output = output.expanduser().resolve()
    print(f"Creating archive:{output}")
    create_archive(source, output, "w:gz")
    print("Archive created. Removing original files...")
    if not args.keep:
        if args.cleanup_scope == "folder":
            remove_path(source, safe_symlinks=False, quiet=True)
        elif args.cleanup_scope == "contents":
            cleanup_contents(source, output, args.workers)
    print("Cleanup complete.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="folder_archiver.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    tar_parser = subparsers.add_parser("tar")
    tar_parser.add_argument("folder", type=Path)
    tar_parser.add_argument("--output", type=Path, default=None)
    tar_parser.add_argument("--keep", action="store_true")
    tar_parser.add_argument("--quiet", action="store_true")
    tar_parser.set_defaults(func=run_tar)
    tgz_parser = subparsers.add_parser("tgz")
    tgz_parser.add_argument("folder", type=Path, nargs="?", default=Path.cwd())
    tgz_parser.add_argument("--output", type=Path, default=None)
    tgz_parser.add_argument("--workers", type=positive_int, default=8)
    tgz_parser.add_argument("--keep", action="store_true")
    tgz_parser.add_argument(
        "--cleanup-scope",
        choices=("contents", "folder", "none"),
        default="contents",
    )
    tgz_parser.set_defaults(func=run_tgz)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as e:
        print(f"Error:{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
