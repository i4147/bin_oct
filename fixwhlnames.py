#!/data/data/com.termux/files/usr/bin/env python
"""You are tasked with recreating a Python command-line utility from scratch. Write a complete, self-contained, runnable Python 3 script that fulfills the specification below. Output only the script, with no explanation.

**Purpose**
The script scans a directory of Python wheel files (`.whl`) and processes them to make them compatible with a Termux (Android) environment. It identifies wheels built for platforms that do not match Termux, reads each wheel's metadata, and rewrites platform tags so the wheel can be installed on Termux. Original wheels are backed up before modification.

**Shebang and imports**
- Begin with a Termux-specific shebang pointing to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/env python`.
- Use `from __future__ import annotations`.
- Use standard library modules: `argparse`, `re`, `shutil`, `zipfile`, `email.parser.HeaderParser`, `multiprocessing.Pool`, `pathlib.Path`, and `typing` (`Any`, `Final`).
- Use the third-party `loguru` package for logging.

**Constants (all `Final`)**
- Wheel file suffix: `.whl`
- Metadata path suffix inside a wheel: `.dist-info/METADATA`
- Wheel info path suffix inside a wheel: `.dist-info/WHEEL`
- Backup directory name: `whl_backup`
- Multiprocessing pool worker count: 8
- Two regex tag patterns in a tuple:
  1. A pattern matching the standard wheel filename format `{name}-{version}-{python}-{abi}-{platform}.whl`, where python tags are `py3`, `py2.py3`, `py2`, or `cpNN`; ABI tags are `none`, `abiNN`, or `cpNNm?`; and platform tags are `manylinux*`, `linux`, `win_amd64`, `win32`, or `macosx*`.
  2. A more permissive fallback pattern matching the last three dash-separated components of any `.whl` filename, allowing alphanumerics, dots, dashes, and underscores within each component.
- A compiled regex matching `cp3` followed by a digit (CPython 3.x tag).
- A compiled regex matching a `Tag: X-Y-` line in a WHEEL metadata file, capturing the first two dash-separated parts.

**Type aliases**
- `Metadata` = `dict[str, str]`
- `Tags` = a 3-tuple of strings `(python_tag, abi_tag, platform_tag)`

**Functions to implement**

1. `extract_metadata_from_wheel(wheel_path: Path) -> Metadata | None`
   - Open the wheel as a zip archive.
   - Find entries ending with `.dist-info/METADATA`. If none exist, log a warning using the wheel's filename and return `None`.
   - Read the first matching METADATA file, parse it with `HeaderParser`, and return its headers as a dict of string to string.
   - Wrap in error handling: on `zipfile.BadZipFile`, or any other exception, log an error and return `None`.

2. Tag extraction helper (e.g., `extract_tags_from_wheel`): reads the `.dist-info/WHEEL` file from the wheel, finds `Tag:` lines, and extracts the python, ABI, and platform tags. It should handle multiple `Tag:` lines by using the first valid one, and return a `Tags` tuple or `None` on failure. Use the `TAG_LINE_PATTERN` regex for the first two components and derive the rest from the complete `Tag:` line value.

3. Wheel filename parsing helper: given a filename, try `TAG_PATTERNS` in order, returning the captured python/ABI/platform tags from the first matching pattern, or `None` if neither matches.

4. Compatibility check helper: determine whether a wheel's tags are incompatible with Termux. A wheel is considered needing rewrite when its platform tag is a generic desktop/other-platform one (for example `win_amd64`, `win32`, `macosx*`, or `manylinux*`) and it is a CPython 3 wheel (matching `CP3_PATTERN` or `py3`), or when its platform tag is `linux_*` or `manylinux*`, which Termux cannot use directly. Pure-Python wheels with `none` ABI and `any` platform are compatible and should be left unchanged.

5. Rewrite helper: for an incompatible wheel, build a new wheel filename that replaces its platform tag with the Termux-compatible platform tag `android_<api>_<arch>` (use `android_24_aarch64` as the default, and let it be overridable through a command-line argument). Update the `Tag:` lines in the WHEEL metadata inside the wheel so they match the new platform tag. Rewrite the archive by copying all entries to a new zip with the updated WHEEL file and the updated filename.

6. Per-file processing function (designed for pool use): takes a wheel path, performs the checks above, backs up the original into the `whl_backup` directory (creating it if needed, next to the source wheels or in the working directory), rewrites the wheel, and returns a result. Catch all exceptions here so one failing wheel doesn't stop the pool. Log success, skip, or error with loguru.

7. `main()`:
   - Parse arguments with `argparse`:
     - A positional or optional directory argument pointing at wheels (default: current directory).
     - An optional `--platform`/`--api`/`--arch` style option to set the target Android tag (default `android_24_aarch64`).
     - An optional `--dry-run` flag that reports what would change without writing.
     - An optional `--workers` option, defaulting to 8.
   - Validate that the directory exists and is a directory; otherwise log an error and exit with non-zero status.
   - Glob for `*.whl` files in the directory (non-recursive). If none found, log that and exit cleanly.
   - Create the backup directory.
   - Process wheels concurrently using `multiprocessing.Pool` with the configured worker count, mapping the per-file function over the list.
   - Summarize results (counts of rewritten, skipped, failed) with loguru.
   - Guard the entry point with `if __name__ == "__main__":` and call `main()`.

**Logging**
- Use `loguru.logger` throughout with brace-style formatting (`logger.info("... {}", value)`).
- Log at info level for normal progress, warning for skipped/undetected metadata, and error for failures.

**Edge cases and error handling**
- Corrupt or non-zip wheels: catch `zipfile.BadZipFile` and log an error, do not crash.
- Wheels without METADATA or WHEEL files: warn and skip.
- Wheel filenames that match neither regex pattern: skip with a warning.
- Wheels already compatible: skip without modification.
- Backup must happen before any rewrite; if backup fails, do not rewrite.
- Write the rewritten wheel to a temporary path and replace the original atomically only on success, so failures leave the original intact.
- Use `shutil` for file copying/moving operations.
- Handle filenames with multiple dots and dashes correctly.

**Execution and usage**
- Runs as a standalone script: `python <script>.py [directory] [options]`.
- Requires the `loguru` package to be installed.
- Designed for Termux on Android; the shebang reflects this.
- Output is the modified wheels in place (originals backed up) plus loguru log messages to stderr.

Output only the complete Python script.
---"""

from __future__ import annotations

import argparse
import re
import shutil
import zipfile
from email.parser import HeaderParser
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Final

from loguru import logger

WHEEL_SUFFIX: Final[str] = ".whl"
METADATA_SUFFIX: Final[str] = ".dist-info/METADATA"
WHEEL_METADATA_SUFFIX: Final[str] = ".dist-info/WHEEL"
BACKUP_DIR_NAME: Final[str] = "whl_backup"
POOL_WORKERS: Final[int] = 8
TAG_PATTERNS: Final[tuple[str, ...]] = (
    (
        r".*?-.*?-.*?-(py3|py2\.py3|py2|cp[0-9]+)-(none|abi[0-9]+|cp[0-9]+m?)-"
        r"(manylinux[0-9_]+|linux|win_amd64|win32|macosx[0-9_]+)\.whl$"
    ),
    (
        r".*?-.*?-.*?-([a-z0-9]+(?:[\.\-][a-z0-9]+)?)-"
        r"([a-z0-9]+(?:[\.\-][a-z0-9]+)?)-"
        r"([a-z0-9_]+(?:[\.\-][a-z0-9_]+)?)\.whl$"
    ),
)
CP3_PATTERN: Final[re.Pattern[str]] = re.compile(r"cp3[0-9]")
TAG_LINE_PATTERN: Final[re.Pattern[str]] = re.compile(r"Tag: (.*?)-(.*?)-")
Metadata = dict[str, str]
Tags = tuple[str, str, str]


def extract_metadata_from_wheel(wheel_path: Path) -> Metadata | None:
    try:
        with zipfile.ZipFile(wheel_path, "r") as zf:
            metadata_files = [f for f in zf.namelist() if f.endswith(METADATA_SUFFIX)]
            if not metadata_files:
                logger.warning("No METADATA file found in {}", wheel_path.name)
                return None
            with zf.open(metadata_files[0]) as f:
                content = f.read().decode("utf-8", errors="ignore")
            parser = HeaderParser()
            msg = parser.parsestr(content)
            name = msg.get("Name")
            version = msg.get("Version")
            if name and version:
                return {"name": name, "version": version}
            logger.warning("Could not find Name/Version in METADATA of {}", wheel_path.name)
            return None
    except zipfile.BadZipFile:
        logger.error("{} is not a valid zip file", wheel_path.name)
        return None
    except Exception as e:
        logger.error("Error reading {}: {}", wheel_path.name, e)
        return None


def extract_wheel_tags(filename: str) -> Tags | None:
    for pattern in TAG_PATTERNS:
        match = re.search(pattern, filename)
        if match:
            return match.group(1), match.group(2), match.group(3)
    if "cp3" in filename:
        py_match = CP3_PATTERN.search(filename)
        if py_match:
            return py_match.group(0), "none", "any"
    return None


def reconstruct_wheel_name(wheel_path: Path, metadata: Metadata, original_filename: str) -> str | None:
    name = metadata["name"]
    version = metadata["version"]
    tags = extract_wheel_tags(wheel_path.name)
    if tags:
        python_tag, abi_tag, platform_tag = tags
        return f"{name}-{version}-{python_tag}-{abi_tag}-{platform_tag}.whl"
    try:
        with zipfile.ZipFile(wheel_path, "r") as zf:
            wheel_files = [f for f in zf.namelist() if f.endswith(WHEEL_METADATA_SUFFIX)]
            if wheel_files:
                with zf.open(wheel_files[0]) as f:
                    content = f.read().decode("utf-8", errors="ignore")
                    if "Root-Is-Purelib: true" in content:
                        py_match = TAG_LINE_PATTERN.search(content)
                        if py_match:
                            python_tag = py_match.group(1)
                            abi_tag = py_match.group(2) or "none"
                            return f"{name}-{version}-{python_tag}-{abi_tag}-any.whl"
    except (zipfile.BadZipFile, KeyError, OSError) as e:
        logger.error("Error reading WHEEL metadata from {}: {}", wheel_path.name, e)
    logger.warning(
        "Could not determine tags for {}, using generic 'py3-none-any'",
        wheel_path.name,
    )
    return f"{name}-{version}-py3-none-any.whl"


def _process_single_file(path: Path, dry_run: bool, backup_dir: Path | None) -> tuple[bool, str | None]:
    print("[{}] Processing", path.name)
    metadata = extract_metadata_from_wheel(path)
    if not metadata:
        return False, path.name
    proper_name = reconstruct_wheel_name(path, metadata, path.name)
    if not proper_name:
        return False, path.name
    if proper_name == path.name:
        print("Already has correct name: {}", path.name)
        return False, None
    if dry_run:
        print("Would rename to: {}", proper_name)
        return True, None
    if backup_dir is not None:
        backup_path = backup_dir / path.name
        shutil.copy2(path, backup_path)
        print("Backup created: {}", backup_path.name)
    try:
        new_path = path.parent / proper_name
        path.rename(new_path)
        logger.success("Renamed to: {}", proper_name)
        return True, None
    except OSError as e:
        logger.error("Error renaming {}: {}", path.name, e)
        return False, path.name


def fix_whl_files_by_metadata(directory: str = ".", dry_run: bool = True, backup: bool = True) -> tuple[int, list[str]]:
    path = Path(directory)
    whl_files = sorted(path.glob(f"*{WHEEL_SUFFIX}"))
    if not whl_files:
        logger.warning("No .whl files found in {}", directory)
        return 0, []
    print("Found {} .whl files", len(whl_files))
    renamed_count = 0
    failed_files: list[str] = []
    backup_dir: Path | None = None
    if backup and not dry_run:
        backup_dir = path / BACKUP_DIR_NAME
        backup_dir.mkdir(exist_ok=True)
        print("Backups will be saved to: {}", backup_dir)
    for idx, path in enumerate(whl_files, 1):
        print("[{}/{}] Processing: {}", idx, len(whl_files), path.name)
        renamed, failed = _process_single_file(path, dry_run, backup_dir)
        if renamed:
            renamed_count += 1
        if failed is not None:
            failed_files.append(failed)
    print("=" * 40)
    print("SUMMARY:")
    print("Total files: {}", len(whl_files))
    if not dry_run:
        print("Successfully renamed: {}", renamed_count)
        print("Failed: {}", len(failed_files))
        if failed_files:
            print("Failed files: {}", ", ".join(failed_files))
    else:
        print("Would rename: {} files", renamed_count)
        print("Would skip/error: {}", len(failed_files))
    if dry_run and renamed_count > 0:
        print("Dry run complete. Run with --apply to apply changes.")
    return renamed_count, failed_files


def _extract_info_worker(wheel_path: Path) -> tuple[str, Metadata | None, str | None]:
    metadata = extract_metadata_from_wheel(wheel_path)
    if not metadata:
        return wheel_path.name, None, None
    proper_name = reconstruct_wheel_name(wheel_path, metadata, wheel_path.name)
    return wheel_path.name, metadata, proper_name


def batch_fix_with_parallel(directory: str = ".") -> None:
    path = Path(directory)
    whl_files = sorted(path.glob(f"*{WHEEL_SUFFIX}"))
    if not whl_files:
        logger.warning("No .whl files found in {}", directory)
        return
    print("Processing {} files with {} workers...", len(whl_files), POOL_WORKERS)
    results: list[tuple[str, Metadata | None, str | None]] = []
    with Pool(processes=POOL_WORKERS) as pool:
        async_results: list[Any] = [pool.apply_async(_extract_info_worker, (f,)) for f in whl_files]
        for ar in async_results:
            try:
                results.append(ar.get())
            except Exception as e:
                logger.error("Error processing file: {}", e)
    print("Extracted information:")
    for old_name, metadata, proper_name in results:
        if metadata is None:
            logger.warning("{} -> <no metadata>", old_name)
        else:
            print(
                "{} -> {} {} -> {}",
                old_name,
                metadata["name"],
                metadata["version"],
                proper_name,
            )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=("Fix batch-renamed .whl files by reading METADATA from inside each wheel"),
        epilog=("This is the most accurate method as it extracts the real package name and version."),
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing .whl files (default: current directory)",
    )
    parser.add_argument(
        "--apply",
        "-a",
        action="store_true",
        help="Actually rename files (dry run by default)",
    )
    parser.add_argument(
        "--no-backup",
        "-b",
        default=True,
        action="store_true",
        help="Skip creating backups (backups are created by default)",
    )
    parser.add_argument(
        "--info-only",
        "-i",
        action="store_true",
        help="Only show extracted info without renaming",
    )
    return parser


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()
    if args.info_only:
        print("Extracting wheel information (no renaming):")
        batch_fix_with_parallel(args.directory)
    else:
        fix_whl_files_by_metadata(
            directory=args.directory,
            dry_run=not args.apply,
            backup=not args.no_backup,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
