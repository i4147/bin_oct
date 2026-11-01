#!/data/data/com.termux/files/usr/bin/env python
import argparse
import logging
import sys
from subliminal import download_best_subtitles, save_subtitles, scan_video
from babelfish import Language


def main():
    parser = argparse.ArgumentParser(
        description="A lightweight CLI tool to download English subtitles for movies or videos."
    )
    parser.add_argument("path", help="Path to the video file (e.g., movie.mp4)")
    parser.add_argument(
        "-l", "--language", default="eng", help="Language code for the subtitle (default: 'en' for English)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging to see provider search details"
    )

    args = parser.parse_args()

    # Setup logging level
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    print(f"Scanning video file: {args.path}...")
    try:
        video = scan_video(args.path)
    except Exception as e:
        print(f"Error scanning video file: {e}", file=sys.stderr)
        sys.exit(1)

    target_language = Language(args.language)
    print(f"Searching for '{target_language.name}' subtitles...")

    # Download the best matching subtitles
    subtitles = download_best_subtitles({video}, {target_language})

    if subtitles[video]:
        save_subtitles(video, subtitles[video])
        print(f"Success! Downloaded {len(subtitles[video])} subtitle file(s) for '{args.path}'.")
    else:
        print("No matching subtitles found across providers.", file=sys.stderr)


if __name__ == "__main__":
    main()
