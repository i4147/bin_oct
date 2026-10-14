#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes an audio file path from the command line, extracts the final five minutes of that recording, and saves the extracted segment as a high-quality MP3 file in the current working directory. The script should display progress messages to the user while it loads the audio, reports the total length of the original recording in minutes, and confirms when the export is complete. If the source audio is shorter than five minutes, the script should export the entire recording rather than failing. The output should be a single MP3 file named last_5_minutes.mp3, encoded at a high bitrate of 320 kbps with a 44.1 kHz sample rate. The script should handle the case where the input file path is missing by exiting gracefully with a usage message, and it should be runnable directly from the command line.
---"""

from __future__ import annotations
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
