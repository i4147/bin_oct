#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script that downloads English subtitles for a local video file using the subliminal library, with the following requirements:

Create a single-file Python command-line script intended to run under Termux on Android (shebang pointing to the Termux Python path, with `from __future__ import annotations` at the top). It should use the `logging` module with `basicConfig` at INFO level and the format `%(asctime)s - %(name)s - %(levelname)s - %(message)s`, with a module-level logger named after `__name__`.

Dependencies: the `babelfish` library for language codes and the `subliminal` library, specifically `download_best_subtitles` and `save_subtitles` from the package root, and `scan_video` from `subliminal.video`. Use `pathlib.Path` for all file handling.

Core function `download_subtitles_advanced(mkv_path, output_dir=None)`:
- Convert the input path to a `Path`. If the file does not exist, log an error stating the file was not found and return `False`.
- If no output directory is given, default to the video file's parent directory. Otherwise convert it to a `Path` and create it (including parents) if missing, without failing if it already exists.
- Scan the video with `scan_video` inside a try block. On failure, log an error describing the scan problem and return `False`. On success, print a line `Processing: <video name>` to stdout.
- Use the provider list in this order: opensubtitles, podnapisi, addic7ed, tvsubtitles.
- Target language is English, represented as `babelfish.Language("eng")`.
- Call `download_best_subtitles` with the scanned video in a list, a set containing the English language, and the providers keyword argument, inside a try block.
- Retrieve the subtitles for this video from the returned mapping, defaulting to an empty dict. If none are found, log a warning "No English subtitles found" and return `False`.
- Build the output path as `<output_dir>/<video stem>.en.srt`.
- Save the subtitles with `save_subtitles` into that location, then report success (log or print the saved path) and return `True`. Wrap the download and save stage in error handling that logs the failure and returns `False` rather than crashing.

Entry point: when run as a script, read the video path from the first command-line argument (`sys.argv[1]`), optionally accept a second argument as the output directory, call the function, and exit with status 0 on success or 1 on failure. If no path argument is provided, print a usage message to stderr and exit with status 1.

Edge cases to handle: missing input file, nonexistent output directory (create it), scanning failures on unsupported or corrupt files, providers returning no results, and network/provider exceptions during download. Keep the script minimal, with clear error messages and no external configuration files. Do not add credential handling beyond what subliminal supports by default.
---"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import babelfish
from subliminal import download_best_subtitles, save_subtitles
from subliminal.video import scan_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def download_subtitles_advanced(mkv_path, output_dir=None):
    mkv_path = Path(mkv_path)
    if not mkv_path.exists():
        logger.error(f"File not found: {mkv_path}")
        return False
    if output_dir is None:
        output_dir = mkv_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    try:
        video = scan_video(mkv_path)
        print(f"Processing: {video.name}")
    except Exception as e:
        logger.error(f"Error scanning: {e}")
        return False
    providers = ["opensubtitles", "podnapisi", "addic7ed", "tvsubtitles"]
    language = babelfish.Language("eng")
    try:
        subtitles = download_best_subtitles([video], {language}, providers=providers)
        video_subtitles = subtitles.get(video, {})
        if not video_subtitles:
            logger.warning("No English subtitles found")
            return False
        subtitle_path = output_dir / f"{mkv_path.stem}.en.srt"
        save_subtitles(video, video_subtitles, single=True, path=subtitle_path)
        print(f"✓ Subtitles saved: {subtitle_path}")
        return True
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python subtitle_downloader.py <movie.mkv> [output_dir]")
        sys.exit(1)
    success = download_subtitles_advanced(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    sys.exit(0 if success else 1)
