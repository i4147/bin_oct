#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a given directory (or the current working directory by default) for Python source files, and then strips or simplifies their content in a bulk, parallel fashion. The tool should accept an optional path argument from the command line and an optional setting for the number of concurrent workers, defaulting to a sensible value based on the available CPU cores (capped at 8). If no Python files are found at the given location, it should exit with a clear error message.
The script should work with a set of transformation options that aggressively reduce the code: removing all comments, docstrings, and type annotations, collapsing excess blank lines, while leaving commented-out code untouched. The transformations must be performed on temporary working copies of each file so that the processing is safe and isolated, with the results written out in a way that keeps the process reliable and avoids leaving partial or corrupted output behind. Backups should not be created, and the tool should operate in live (non-dry-run) mode by default.
Key behaviors to satisfy:
- Discover all Python files recursively under the provided path.
- Copy each source file into a temporary workspace before processing, using unique, collision-free names.
- Apply the configured minification-style transformations to each file, handling syntax errors or unreadable files gracefully without stopping the whole batch.
- Run the work concurrently across files using the requested number of workers.
- Report progress and a final summary (files processed, succeeded, failed, and elapsed time).
- Clean up all temporary resources automatically when finished, even if errors occur.
---"""

from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import tempfile
import time
import rmc3 as sc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("-j", "--jobs", type=int, default=min(8, sc.os.cpu_count() or 1))
    args = parser.parse_args()
    sources = list(sc.iter_python_files([args.path], []))
    if not sources:
        parser.error("no Python files found")
    options = sc.TransformOptions(
        remove_all=True,
        remove_all_comments=True,
        remove_docstrings=True,
        remove_type_annotations=True,
        remove_commented_code=False,
        collapse_blank_lines=True,
        make_backup=False,
        overwrite_backup=False,
        dry_run=False,
    )
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        copies = []
        for number, source in enumerate(sources):
            destination = root / f"{number}{source.suffix}"
            shutil.copyfile(source, destination)
            copies.append(destination)
        started = time.perf_counter()
        results = list(sc._result_iterator(copies, options, args.jobs, sc.DEFAULT_CHUNK_SIZE))
        elapsed = time.perf_counter() - started
    errors = sum(result.error is not None for result in results)
    total_bytes = sum(result.old_size for result in results)
    rate = len(results) / elapsed if elapsed else float("inf")
    mib_rate = total_bytes / (1024 * 1024) / elapsed if elapsed else float("inf")
    print(f"files={len(results)} bytes={total_bytes} seconds={elapsed:.3f}")
    print(f"throughput={rate:.1f} files/s, {mib_rate:.1f} MiB/s, errors={errors}")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
