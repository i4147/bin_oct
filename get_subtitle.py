#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script which, given a path to an MKV video file and an optional output directory, locates and downloads the best English subtitles for that video and saves them alongside or in the specified directory. Specify the following:

Purpose: A command-line utility for Termux (Android) that fetches English subtitles for a local MKV video using the subliminal library and babelfish for language codes.

Environment and shebang: Use the Termux Python path shebang (`#!/data/data/com.termux/files/usr/bin/env python`) and include `from __future__ import annotations` at the top.

Dependencies: `babelfish`, `subliminal` (including `subliminal.providers.ProviderError` and `subliminal.video.scan_video`, plus `download_best_subtitles` and `save_subtitles`), plus standard library `logging`, `sys`, and `pathlib.Path`.

Logging: Configure root logging at INFO level with the format `%(asctime)s - %(levelname)s - %(message)s`, and create a module-level logger using `__name__`.

Core function `get_english_subtitles(mkv_path, output_dir=None)`:
- Convert the input to a `Path`. If the file does not exist, log an error and return `False`.
- If the suffix is not `.mkv` (case-insensitive), log a warning but continue processing.
- If `output_dir` is not given, default to the video's parent directory. Otherwise convert it to a `Path` and create it (including parents) if missing.
- Print the scanning message, then call `scan_video`. On success print the video name, size in bytes, duration formatted to two decimal places in seconds, and hashes. On any exception, log an error and return `False`.
- Create the language object with `babelfish.Language("eng")` and print that English subtitles are being searched.
- Call `download_best_subtitles` for the scanned video with English as the only requested language, handling `ProviderError` and other exceptions with logged errors and a `False` return.
- If no subtitles are found, log a message and return `False`. Otherwise save the best subtitle(s) with `save_subtitles` into the output directory, log each saved file, and return `True` on success.

Entry point: When run as a script, read the MKV path from the first command-line argument (via `sys.argv`) and optionally the output directory from the second argument. If no path is given, print a usage message and exit with a non-zero status. Call `get_english_subtitles` and exit with status 0 on success or 1 on failure.

Edge cases to handle: nonexistent files, non-MKV extensions (warning only), missing or newly created output directories, scan failures, provider errors, network failures during subtitle search, and no subtitles found. Use `Path` consistently and avoid hard-coded absolute paths except the shebang.
---"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import babelfish
from subliminal import download_best_subtitles, save_subtitles
from subliminal.providers import ProviderError
from subliminal.video import scan_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_english_subtitles(mkv_path, output_dir=None):
    mkv_path = Path(mkv_path)
    if not mkv_path.exists():
        logger.error(f"File not found: {mkv_path}")
        return False
    if mkv_path.suffix.lower() != ".mkv":
        logger.warning(f"File is not an MKV: {mkv_path}")
    if output_dir is None:
        output_dir = mkv_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Scanning video: {mkv_path}")
    try:
        video = scan_video(mkv_path)
        print(f"Found video: {video.name}")
        print(f"  - Size: {video.size} bytes")
        print(f"  - Duration: {video.duration:.2f} seconds")
        print(f"  - Hashes: {video.hashes}")
    except Exception as e:
        logger.error(f"Error scanning video: {e}")
        return False
    language = babelfish.Language("eng")
    print("Searching for English subtitles...")
    try:
        subtitles = download_best_subtitles(
            [video],
            {language},
            providers=["opensubtitles", "podnapisi", "addic7ed", "tvsubtitles"],
        )
        video_subtitles = subtitles.get(video, {})
        if not video_subtitles:
            logger.warning(f"No English subtitles found for {mkv_path.name}")
            return False
        subtitle_path = output_dir / f"{mkv_path.stem}.srt"
        save_subtitles(video, video_subtitles, single=True, path=subtitle_path)
        print(f"Subtitles saved to: {subtitle_path}")
        return True
    except ProviderError as e:
        logger.error(f"Provider error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error downloading subtitles: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python subtitle_downloader.py <path_to_mkv_file> [output_directory]")
        print("Example: python subtitle_downloader.py movie.mkv")
        print("Example: python subtitle_downloader.py /path/to/movie.mkv /path/to/subtitles/")
        sys.exit(1)
    mkv_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    success = get_english_subtitles(mkv_path, output_dir)
    if success:
        print("✓ Subtitles downloaded successfully!")
    else:
        print("✗ Failed to download subtitles.")
        sys.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
