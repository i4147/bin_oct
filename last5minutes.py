#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that takes an audio file path as its first argument and extracts the final portion of that audio using moviepy's AudioFileClip.
It should compute the clip's total duration, determine a start time roughly 230 seconds before the end (clamped to 0 if the file is shorter), and extract the subclip from that start time to the end.
The resulting audio segment should be exported as "last_5_minutes.mp3" at 320k bitrate and 44100 fps, with console messages printed before and after processing to indicate progress and completion."""

import sys
from moviepy import AudioFileClip

if __name__ == "__main__":
    file = sys.argv[1]
    output = "last_5_minutes.mp3"
    print("Loading file and extracting last 5 minutes...")
    audio = AudioFileClip(file)
    duration = audio.duration
    start_time = max(0, duration - 230)
    clip = audio.subclipped(start_time, duration)
    print(f"Writing {output} ({duration / 60:.1f} min total → last 5 min)...")
    clip.write_audiofile(output, bitrate="320k", fps=44100)
    print("Done! 🎉")
