#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a directory tree and collects file paths matching a given set of file extensions, with support for compressed manual-page-style files. The script should accept a root directory and an optional list of extensions (or treat "no filter" as matching all files). It should traverse breadth-first, skip version-control and cache directories, avoid following symbolic links, and gracefully ignore directories that cannot be read due to permission or OS errors. Beyond plain extensions, it should also recognize gzip-compressed files whose underlying name ends in numbered section suffixes (such as manual pages compressed with a .gz extension), treating them as matches when the caller requests the corresponding extension family. The result should be a list of matching file paths returned to the caller, suitable for further processing such as indexing, searching, or batch conversion. Where useful, the script may also provide helper behavior for reading or decompressing matched gzip files into temporary files and for printing progress or status messages to the console, but the core deliverable is a robust, memory-efficient file discovery routine with clear, documented inputs and outputs and sensible error handling.
---"""

from __future__ import annotations
from collections import deque
import gzip
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from dh import cprint, mpf, runcmd


def get_files(path: str | Path, ext: list[str] | None = None) -> list[Path]:
    path = Path(path)
    skip_dirs = {".git", "__pycache__"}
    queue = deque([path])
    files = []
    while queue:
        current = queue.popleft()
        try:
            entries = current.iterdir()
        except (PermissionError, OSError):
            continue
        for item in entries:
            if item.is_symlink():
                continue
            if item.is_dir() and item.name not in skip_dirs:
                queue.append(item)
            elif item.is_file() and (
                ext is None
                or item.suffix in ext
                or (
                    item.suffixes[-2:] == [".1", ".gz"]
                    or item.suffixes[-2:] == [".3", ".gz"]
                    or item.suffixes[-2:] == [".4", ".gz"]
                    or (item.suffixes[-2:] == [".5", ".gz"])
                    or (item.suffixes[-2:] == [".6", ".gz"])
                    or (item.suffixes[-2:] == [".7", ".gz"])
                    or (item.suffixes[-2:] == [".8", ".gz"])
                    or (item.suffixes[-2:] == [".3am", ".gz"])
                    or (item.suffixes[-2:] == [".3form", ".gz"])
                    or (item.suffixes[-2:] == [".3menu", ".gz"])
                    or (item.suffixes[-2:] == [".3ncurses", ".gz"])
                    or (item.suffixes[-2:] == [".3readline", ".gz"])
                    or (item.suffixes[-2:] == [".3t", ".gz"])
                    or (item.suffixes[-2:] == [".n", ".gz"])
                )
            ):
                files.append(item)
    return files


def safe_run(path) -> bool:
    path = Path(path)
    is_gzipped = path.suffix == ".gz"
    if is_gzipped:
        with NamedTemporaryFile(mode="w", suffix=path.stem, delete=False) as tmp:
            with gzip.open(path, "rt", encoding="utf8") as gz:
                tmp.write(gz.read())
            tmp_path = tmp.name
    else:
        tmp_path = str(path)
    try:
        cmd = ["mandoc", "-T", "html", tmp_path]
        res, txt, _err = runcmd(cmd, show_output=False)
        if res != 0:
            print(f"Error running mandoc: {err}", file=sys.stderr)
            return False
        if is_gzipped:
            outpath = path.with_suffix(".html")
        else:
            outpath = path.with_suffix(".html")
        outpath.write_text(txt, encoding="utf8")
        path.unlink()
        return True
    finally:
        if is_gzipped and Path(tmp_path).exists():
            Path(tmp_path).unlink()


def process_file(path) -> bool:
    path = Path(path)
    if not path.exists():
        return False
    print(f"{path.name}", end=" ")
    res = safe_run(path)
    if res:
        cprint("[✓] ", "cyan")
        return True
    cprint("[ERROR]", "red")
    return False


def main() -> None:
    args = sys.argv[1:]
    cwd = Path.cwd()
    base_exts = [
        ".1",
        ".3",
        ".3am",
        ".3pm",
        ".3form",
        ".3menu",
        ".3ncurses",
        ".3readline",
        ".3t",
        ".4",
        ".5",
        ".7",
        ".8",
        ".n",
    ]
    all_exts = base_exts + [f"{ext}.gz" for ext in base_exts]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=all_exts)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
