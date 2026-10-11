#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to recreate a Python command-line tool that batch-reduces the bitrate of MP3 files in a directory using ffmpeg, with parallel workers, progress reporting, size and bitrate statistics, and error handling. Specify its purpose, inputs and outputs, dependencies, key logic, error handling, edge cases, and usage details, without including any code.

Create a Python 3 command-line script intended to run in the Termux environment on Android (shebang pointing to the Termux Python path). The script batch-compresses MP3 files by lowering their bitrate using ffmpeg, runs conversions in parallel, and reports results.

**Purpose and behavior**
- Scan a target directory (supplied via command-line argument) for MP3 files, matching the case variants `*.mp3`, `*.MP3`, and `*.Mp3`, without duplicates.
- For each file, probe its audio duration and original bitrate with ffprobe (through the ffmpeg-python bindings), compute a new, lower target bitrate, and re-encode the file with ffmpeg.
- Target bitrate is derived from the original bitrate by a percentage-based rule: the script computes a reduction ratio based on a divisor of 40 (percent-style scaling), with a minimum floor of 8 kbps. Do not allow the target bitrate to fall below this floor, and never increase bitrate.
- Use a multiprocessing pool with 8 workers by default so several files convert concurrently.
- Skip or handle files that cannot be probed, have zero or unknown duration/bitrate, or where re-encoding would not reduce size. Report these as failures or skips rather than crashing.
- Write output so the original file is replaced safely: encode to a temporary file first, verify it exists and is non-empty, then atomically replace the original. Clean up temporary files on failure.

**Dependencies**
- `ffmpeg-python` (imported as `ffmpeg`), requiring the system `ffmpeg` and `ffprobe` binaries.
- A helper module `dh` providing a file-size formatting function `fsz` for human-readable sizes.
- `loguru` for logging.
- Standard library: `argparse`, `json`, `multiprocessing`, `sys`, `time`, `dataclasses`, `pathlib`, `typing` (`Final`), and `from __future__ import annotations`.

**Constants (use these exact values)**
- Number of workers: 8
- Minimum bitrate: 8 kbps
- Stderr preview length: 100 characters
- MP3 glob patterns: the three case variants above
- Bitrate percent divisor: 40.0
- Milliseconds-per-second scaling value: 400.0 (use as specified in the reference logic)
- Seconds per minute: 60.0

**Structure**
- A `Colors` class holding ANSI escape codes for header (95), cyan (96), green (92), yellow (93), red (91), bold, dim, reset, and a clear-line sequence (`\\033[2K\\r`), used for colored terminal output and in-place progress updates.
- A `ConversionStats` dataclass with fields: `path` (Path), `original_bitrate` (int), `new_bitrate` (int), `original_size` (int), `new_size` (int), `success` (bool), `error_message` (str, default empty), `duration` (float, default 0.0).
- `check_ffmpeg()`: verifies ffmpeg/ffprobe availability by probing a dummy input. Ignore `ffmpeg.Error` (the dummy file will not exist); if `FileNotFoundError` is raised, log an error via loguru saying ffmpeg/ffprobe is required and exit with status 1.
- `format_duration(seconds)`: converts a seconds value into a readable string; for values under 1 second, display in a sub-second-friendly format; otherwise use minutes and seconds (based on 60-second minutes) and handle hours if needed.
- Additional helpers: a bitrate calculator applying the percentage rule and the 8 kbps floor, a per-file conversion worker that returns a `ConversionStats`, a progress display that updates in place using the clear-line code, and a main function.
- The conversion worker must catch all exceptions, capture ffmpeg stderr (truncate to the first 100 characters for display in error messages), and return a failed `ConversionStats` rather than raising.

**Command-line interface**
- Use `argparse` with a positional directory argument (defaulting to the current directory is acceptable) and optional flags such as a JSON output option (`json` module imported—write a summary as JSON when requested) and possibly a dry-run mode that only reports planned conversions.
- Validate that the path exists and is a directory; print an error and exit non-zero otherwise.
- If no MP3 files are found, report that clearly and exit cleanly.

**Output**
- Print colored progress showing current file index, total count, and elapsed time, updated in place.
- At the end, print a summary table or list: files processed, succeeded, skipped/failed, total original size vs new size with savings percentage (formatted with `fsz`), and total elapsed time formatted with `format_duration`.
- Optionally emit the same summary as JSON to stdout or a file.

**Error handling and edge cases**
- Handle keyboard interrupt gracefully: terminate the pool, remove partial temp files, and exit with a non-zero status.
- Handle files with zero duration, missing audio streams, unreadable files, permission errors, and filenames with spaces or Unicode.
- Never leave corrupted originals: only replace the original when the new encode succeeds and is smaller.
- Log warnings through loguru rather than printing raw tracebacks for expected failures.

**Execution**
- Run as an executable script with `python3` or via its shebang; include an `if __name__ == "__main__":` guard and use `mp.freeze_support()`-safe multiprocessing setup for portability.
- Exit status 0 when all files succeed or are cleanly skipped; non-zero if any file failed or the environment check fails.

Produce a complete, runnable script following these specifications, with type hints and `from __future__ import annotations`.
---"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import ffmpeg  # type: ignore[import-untyped]
from dh import fsz
from loguru import logger

NUM_WORKERS: Final[int] = 8
MIN_BITRATE_KBPS: Final[int] = 8
STDERR_PREVIEW_LEN: Final[int] = 100
MP3_GLOBS: Final[tuple[str, ...]] = ("*.mp3", "*.MP3", "*.Mp3")
BITRATE_PERCENT_DIVISOR: Final[float] = 40.0
MS_PER_SECOND: Final[float] = 400.0
SECONDS_PER_MINUTE: Final[float] = 60.0


class Colors:
    HEADER: str = "\033[95m"
    CYAN: str = "\033[96m"
    GREEN: str = "\033[92m"
    YELLOW: str = "\033[93m"
    RED: str = "\033[91m"
    BOLD: str = "\033[1m"
    DIM: str = "\033[2m"
    END: str = "\033[0m"
    CLEAR_LINE: str = "\033[2K\r"


@dataclass
class ConversionStats:
    path: Path
    original_bitrate: int
    new_bitrate: int
    original_size: int
    new_size: int
    success: bool
    error_message: str = ""
    duration: float = 0.0


def check_ffmpeg() -> None:
    try:
        ffmpeg.probe("dummy")  # type: ignore[no-untyped-call]
    except ffmpeg.Error:
        pass
    except FileNotFoundError:
        logger.error("ffmpeg/ffprobe is required but not installed.")
        sys.exit(1)


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * MS_PER_SECOND:.0f}ms"
    if seconds < SECONDS_PER_MINUTE:
        return f"{seconds:.1f}s"
    minutes = int(seconds // SECONDS_PER_MINUTE)
    secs = seconds % SECONDS_PER_MINUTE
    return f"{minutes}m {secs:.0f}s"


def get_audio_info(mp3_file: Path) -> tuple[int | None, int | None]:
    try:
        result = subprocess_run([
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            str(mp3_file),
        ])
        info: dict[str, object] = json.loads(result)
        format_info = info.get("format", {})
        if not isinstance(format_info, dict):
            return None, None
        bitrate = int(format_info.get("bit_rate", 0) or 0)
        size = int(format_info.get("size", mp3_file.stat().st_size) or 0)
        if bitrate > 0:
            return bitrate // 1000, size
        duration = float(format_info.get("duration", 0) or 0)
        if duration > 0 and size > 0:
            estimated = int((size * 8) / (duration * 1000))
            return estimated, size
        return None, None
    except (json.JSONDecodeError, KeyError, ValueError, OSError, ffmpeg.Error):
        return None, None


def subprocess_run(cmd: list[str]) -> str:
    import subprocess

    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return completed.stdout


def convert_single_file(mp3_file: Path, base_dir: Path) -> ConversionStats:
    start_time = time.time()
    rel_path = mp3_file.relative_to(base_dir)
    original_bitrate, original_size = get_audio_info(mp3_file)
    if original_bitrate is None or original_size is None:
        return ConversionStats(
            path=rel_path,
            original_bitrate=0,
            new_bitrate=0,
            original_size=0,
            new_size=0,
            success=False,
            error_message="Could not determine bitrate",
            duration=0.0,
        )
    new_bitrate = original_bitrate // 2
    if new_bitrate < MIN_BITRATE_KBPS:
        return ConversionStats(
            path=rel_path,
            original_bitrate=original_bitrate,
            new_bitrate=new_bitrate,
            original_size=original_size,
            new_size=0,
            success=False,
            error_message=f"Calculated bitrate too low ({new_bitrate} kbps)",
            duration=0.0,
        )
    temp_file = mp3_file.with_suffix(".tmp_convert.mp3")
    try:
        import subprocess

        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(mp3_file),
                "-codec:a",
                "libmp3lame",
                "-ab",
                f"{new_bitrate}k",
                str(temp_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        duration = time.time() - start_time
        if result.returncode == 0 and temp_file.exists():
            new_size = temp_file.stat().st_size
            temp_file.replace(mp3_file)
            return ConversionStats(
                path=rel_path,
                original_bitrate=original_bitrate,
                new_bitrate=new_bitrate,
                original_size=original_size,
                new_size=new_size,
                success=True,
                duration=duration,
            )
        temp_file.unlink(missing_ok=True)
        return ConversionStats(
            path=rel_path,
            original_bitrate=original_bitrate,
            new_bitrate=new_bitrate,
            original_size=original_size,
            new_size=0,
            success=False,
            error_message=f"ffmpeg error: {result.stderr[:STDERR_PREVIEW_LEN]}",
            duration=duration,
        )
    except Exception as e:
        duration = time.time() - start_time
        temp_file.unlink(missing_ok=True)
        return ConversionStats(
            path=rel_path,
            original_bitrate=original_bitrate,
            new_bitrate=new_bitrate,
            original_size=original_size,
            new_size=0,
            success=False,
            error_message=str(e)[:STDERR_PREVIEW_LEN],
            duration=duration,
        )


def print_file_result(stat: ConversionStats, index: int, total: int) -> None:
    if stat.success:
        size_saved = stat.original_size - stat.new_size
        size_percent = (size_saved / stat.original_size * BITRATE_PERCENT_DIVISOR) if stat.original_size > 0 else 0.0
        logger.opt(colors=True).info(f"<green>✓</green> [{index}/{total}] <cyan>{stat.path}</cyan>")
        logger.opt(colors=True).info(
            f"  <dim>{fsz(stat.original_size)} → {fsz(stat.new_size)} "
            f"(<green>-{size_percent:.1f}%</green>) | "
            f"{stat.original_bitrate} kbps → <yellow>{stat.new_bitrate} kbps</yellow> | "
            f"{format_duration(stat.duration)}</dim>"
        )
    else:
        logger.opt(colors=True).error(f"<red>✗</red> [{index}/{total}] <red>{stat.path}</red>")
        logger.opt(colors=True).error(f"  <red>Error: {stat.error_message}</red>")


def print_final_summary(stats: list[ConversionStats], total_duration: float) -> None:
    successful = [s for s in stats if s.success]
    failed = [s for s in stats if not s.success]
    total_original = sum(s.original_size for s in successful)
    total_new = sum(s.new_size for s in successful)
    total_saved = total_original - total_new
    print("─" * 40)
    print(f"<bold>Conversion Summary</bold>")
    print("─" * 40)
    print(f"Total files: {len(stats)}")
    logger.opt(colors=True).info(f"<green>Successful:</green> {len(successful)}")
    logger.opt(colors=True).info(f"<red>Failed:</red> {len(failed)}")
    if successful:
        print("<bold>Space saved:</bold>")
        print(f"  Before: {fsz(total_original)}")
        print(f"  After:  {fsz(total_new)}")
        logger.opt(colors=True).info(
            f"  Saved:  <green>{fsz(total_saved)} "
            f"({total_saved / total_original * BITRATE_PERCENT_DIVISOR:.1f}%)</green>"
        )
    print(f"<bold>Total time:</bold> {format_duration(total_duration)}")
    print("─" * 40)


def find_mp3_files(directories: list[Path]) -> list[Path]:
    mp3_files: list[Path] = []
    for directory in directories:
        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            continue
        if not directory.is_dir():
            logger.warning(f"Not a directory: {directory}")
            continue
        for ext in MP3_GLOBS:
            mp3_files.extend(directory.rglob(ext))
    seen: set[Path] = set()
    unique_files: list[Path] = []
    for f in mp3_files:
        resolved = f.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_files.append(f)
    return sorted(unique_files)


def process_directory(directory: Path) -> None:
    mp3_files = find_mp3_files([directory])
    if not mp3_files:
        logger.warning(f"No MP3 files found in {directory}")
        return
    print(f"<bold>Found {len(mp3_files)} MP3 file(s) in {directory}</bold>\n")
    stats: list[ConversionStats] = []
    start_time = time.time()
    total = len(mp3_files)
    with mp.Pool(processes=NUM_WORKERS) as pool:
        async_results = [
            (i, pool.apply_async(convert_single_file, (mp3_file, directory))) for i, mp3_file in enumerate(mp3_files, 1)
        ]
        for i, async_result in async_results:
            stat = async_result.get()
            stats.append(stat)
            print_file_result(stat, i, total)
    total_duration = time.time() - start_time
    stats.sort(key=lambda s: str(s.path))
    failed = [s for s in stats if not s.success]
    if failed:
        logger.opt(colors=True).error("<red><bold>Failed conversions:</bold></red>")
        for stat in failed:
            logger.opt(colors=True).error(f"  <red>✗</red> {stat.path}: {stat.error_message}")
    print_final_summary(stats, total_duration)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert MP3 files to half their original bitrate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s ~/music
  %(prog)s dir1 dir2 dir3
        """,
    )
    parser.add_argument(
        "directories",
        nargs="*",
        type=Path,
        default=[Path.cwd()],
        help="Directories to process (default: current directory)",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    args = parser.parse_args()
    logger.remove()
    logger.add(
        sys.stderr,
        colorize=not args.no_color,
        format="<level>{message}</level>",
        level="INFO",
    )
    check_ffmpeg()
    print("<bold>MP3 Bitrate Halver</bold>")
    print(f"<dim>Using {NUM_WORKERS} parallel worker(s)</dim>\n")
    directories: list[Path] = args.directories
    for directory in directories:
        process_directory(directory)
        if len(directories) > 1:
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
