#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that converts an M4A audio file to MP3 using ffmpeg via a helper "runcmd" function from a local "dh" module.
It should take an input file path and an optional bitrate (default "64k"), validate that the file exists and warn if it lacks the .m4a extension, then build and run the appropriate ffmpeg command to produce an output file with the same name but .mp3 extension.
After conversion it should print the input and output file sizes in MB along with the compression ratio, and it must handle missing ffmpeg or subprocess errors gracefully by printing an error message and exiting with a non-zero status."""

from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path
from dh import runcmd


def convert_m4a_to_mp3(input_file, bitrate="64k"):
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    if not input_file.lower().endswith(".m4a"):
        print("Warning: Input file doesn't have .m4a extension. Proceeding anyway...")
    input_path = Path(input_file)
    output_file = str(input_path.with_suffix(".mp3"))
    print(f"Converting: {input_file}")
    print(f"Output: {output_file}")
    print(f"Bitrate: {bitrate}")
    cmd = [
        "ffmpeg",
        "-i",
        input_file,
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        "-vn",
        "-y",
        output_file,
    ]
    try:
        ret, _txt, _err = runcmd(cmd, show_output=True)
        if not ret:
            print(f"Successfully converted to: {output_file}")
        input_size = os.path.getsize(input_file) / (1024 * 1024)
        output_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"Input size: {input_size:.2f} MB")
        print(f"Output size: {output_size:.2f} MB")
        print(f"Size ratio: {output_size / input_size:.1%}")
    except subprocess.CalledProcessError as e:
        print("Error during conversion:")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg first.")
        print("Ubuntu/Debian: sudo apt install ffmpeg")
        print("macOS: brew install ffmpeg")
        print("Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_file.m4a>")
        print("Example: python script.py song.m4a")
        sys.exit(1)
    input_file = sys.argv[1]
    convert_m4a_to_mp3(input_file, bitrate="64k")
