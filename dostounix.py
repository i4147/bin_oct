#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts text files from Windows-style line endings (CRLF) to Unix-style line endings (LF), in place. The tool should accept one or more file or directory paths as command-line arguments; if no arguments are given, it should process the current working directory. When a directory is provided, it should recursively find all files within it. The tool should skip binary files and any files or directories that match a standard set of exclusion rules (such as version control folders, build artifacts, or caches), which should be determined by helper logic that the implementer may design as they see fit.
Key behaviors:
- Only modify files that actually contain CRLF sequences; leave all other files untouched and do not rewrite their timestamps unnecessarily.
- Perform the conversion safely, for example by writing to a temporary file and atomically replacing the original, so a failure never leaves a partially written file behind.
- Process files in parallel using a pool of worker processes with a sensible default concurrency and chunked task distribution to keep throughput high on large trees.
- Handle errors gracefully per file (such as permission errors or I/O failures) without aborting the entire run; report which files failed and continue with the rest.
- At the end, print a concise summary including the number of files scanned, the number converted, and any errors encountered.
- Ensure the script works correctly when launched as a standalone program and guards its multiprocessing entry point appropriately for cross-platform use.
The implementer is free to choose the structure, libraries, naming, command-line parsing approach, and reporting format, as long as the core purpose and behaviors above are met.
---"""

from __future__ import annotations
from multiprocessing import Pool
from pathlib import Path
import sys
from dh import is_binary, should_skip

WORKERS = 8
CHUNK_SIZE = 64


def _iter_files(paths):
    for raw in paths:
        p = Path(raw).expanduser().resolve()
        if p.is_dir():
            yield from (f for f in p.rglob("*") if f.is_file() and not is_binary(f) and not should_skip(f))
        elif p.is_file() and not is_binary(p) and not should_skip(p):
            yield p


def _collect_files(args: list[str]) -> list[Path]:
    if not args:
        return list(_iter_files([Path.cwd()]))
    return list(_iter_files(args))


def _convert_file(path_str: str) -> tuple[Path, bool, str]:
    path = Path(path_str)
    try:
        data = path.read_bytes()
        if b"\r\n" not in data:
            return (path, False, "")
        new_data = data.replace(b"\r\n", b"\n")
        tmp = path.with_name(path.name + ".dos2unix.tmp")
        tmp.write_bytes(new_data)
        tmp.replace(path)
        return (path, True, "")
    except (OSError, PermissionError) as e:
        return (path, False, f"{e}")


def _run_parallel(files: list[Path]) -> tuple[int, int, list[str]]:
    changed = 0
    errors: list[str] = []
    with Pool(processes=WORKERS) as pool:
        futures = [pool.apply_async(_convert_file, (str(f),)) for f in files]
        for fut in futures:
            try:
                _, was_changed, err = fut.get()
                if was_changed:
                    changed += 1
                if err:
                    errors.append(err)
            except Exception as e:
                errors.append(f"Unexpected error: {e}")
    return (changed, len(files) - changed - len(errors), errors)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert DOS/Windows (CRLF) files to Unix (LF) format in-place.",
        epilog="If no paths are given, processes all files in the current directory recursively.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        metavar="FILE_OR_DIR",
        help="Files or directories to process (recursive for directories).",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress per-file output; only show summary.",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be done without modifying files.",
    )
    args = parser.parse_args(argv)
    files = _collect_files(args.paths)
    if not files:
        print("No files to process.", file=sys.stderr)
        return 0
    if args.dry_run:
        for f in files:
            print(f"Would convert: {f}")
        print(f"\n{len(files)} file(s) would be processed.")
        return 0
    changed, unchanged, errors = _run_parallel(files)
    if not args.quiet:
        for f in files:
            pass
    print(f"Converted: {changed} file(s)")
    print(f"Unchanged: {unchanged} file(s)")
    if errors:
        print(f"Errors: {len(errors)}", file=sys.stderr)
        for e in errors[:10]:
            print(f"  {e}", file=sys.stderr)
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
