#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively walks a given root directory (or accepts a single file path) and collects every file that is eligible for processing, while skipping directories and files that match a set of exclusion rules. The script should avoid revisiting the same directory twice, including through symbolic links, so that it never loops endlessly or processes duplicate content. If the provided path is a single file rather than a directory, the script should treat that file as the only item to process.
For each collected file, the script should check that it exists, and then apply type-specific handling based on the file's extension. For C source files, it should compile or analyze the file using an external C compiler toolchain, reporting success or failure for each file. Other file types should be handled gracefully, either by being skipped or by receiving an appropriate default treatment.
The script should produce clear, human-readable console output summarizing progress and results, including the number of files processed, successes, and failures, along with the path of each file that could not be handled and a brief reason. It should continue processing remaining files when an individual file fails rather than stopping the entire run. Where helpful, it should also report aggregate size information for the processed files, using a readable format for byte counts.
Design the script to be usable both as a standalone command-line tool that accepts a directory or file path as an argument and as an importable module whose core functions can be called from other Python code. Handle missing paths, permission errors, and unexpected external tool failures without crashing.
---"""

from __future__ import annotations
from pathlib import Path
from dh import fsz, gsz, mpf, should_skip


def get_filez(root_dir: str | Path):
    from os import walk as os_walk

    visited_dirs: set[Path] = set()
    root_dir = Path(root_dir)
    if root_dir.is_dir():
        for dirpath, dirnames, filenames in os_walk(root_dir, topdown=True):
            base_path = Path(dirpath)
            for dirname in list(dirnames):
                full_path = base_path / dirname
                resolved_path = full_path.resolve()
                if should_skip(full_path) or resolved_path in visited_dirs:
                    dirnames.remove(dirname)
                visited_dirs.add(resolved_path)
            for filename in filenames:
                path = Path(dirpath) / filename
                if not should_skip(path):
                    yield path
    else:
        yield root_dir


def process_file(path):
    path = Path(path)
    if not path.exists():
        return False
    if path.suffix == ".c":
        cmd = f"clang {path!s} -o {path.with_suffix('')!s}"
    if path.suffix == ".cpp":
        cmd = f"clang++ {path!s} -o {path.with_suffix('')!s}"
    ret, txt, _err = run_command(cmd)
    print(txt)
    return ret


def main() -> None:
    cwd = Path().cwd()
    start_size = gsz(cwd)
    files = []
    for path in get_filez(cwd):
        if path.is_file() and path.suffix in {".c", ".cpp"}:
            files.append(path)
    mpf(process_file, files)
    print(f"{fsz(start_size - gsz(cwd))}")


if __name__ == "__main__":
    raise SystemExit(main())
