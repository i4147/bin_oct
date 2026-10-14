#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts an audio file from M4A format to MP3 format, using a command-line interface. The script should accept an input M4A file path and an optional audio bitrate (defaulting to 64 kbps), and produce an MP3 file with the same base name in the same directory as the input. Before converting, it should ver the input file exists and warn the user if the file does not carry an .m4a extension, while still proceeding. During conversion, it should display progress information including the source file, the destination file, and the chosen bitrate, and stream the external encoder's output to the console. The conversion should discard any video stream and retain only the audio. If the conversion succeeds, the script should report success along with the output location, and then report the file sizes of both the original and the converted file in megabytes so the user can see the size difference. If the input file is missing or the conversion fails, the script should print a clear error message and exit with a non-zero status code. Overwriting an existing output file without prompting is acceptable. Ensure the script is robust, user-friendly, and runs on common desktop operating systems where the required external audio encoding tool is installed.
---"""

from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
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
