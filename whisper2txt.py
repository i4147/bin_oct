#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts an audio recording into a plain-text transcript using a local speech-recognition model. The tool should accept a single audio file path (such as an M4A recording) as a command-line argument and print a brief usage message if the argument is missing or malformed. Before processing, it should verify that the input file exists and exit with a clear error message if it does not. It should load a lightweight, general-purpose speech-to-text model, transcribe the full audio, and save the resulting text to a UTF-8 encoded output file named "out.txt" in the current working directory. Provide informative progress messages to the user during model loading, processing, and saving, and confirm the output location when finished. For convenience, also display a preview of the transcript in the console, truncated to roughly the first 200 characters with an ellipsis if it is longer. The script should be runnable directly from the command line and handle errors gracefully, returning a non-zero exit status on failure.
---"""

from __future__ import annotations
import os
import sys
import whisper


def m4a_to_text_whisper(input_file, output_file="out.txt"):
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    print("Loading Whisper model...")
    model = whisper.load_model("base")
    print(f"Processing: {input_file}")
    result = model.transcribe(input_file)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result["text"])
    print(f"✓ Transcription saved to: {output_file}")
    print(
        f"Transcribed text:\n{result['text'][:200]}..."
        if len(result["text"]) > 200
        else f"Transcribed text:\n{result['text']}"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python m4a_to_text.py <input_file.m4a>")
        sys.exit(1)
    m4a_to_text_whisper(sys.argv[1])
