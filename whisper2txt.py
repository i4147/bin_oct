#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line script that transcribes an audio file (e.g., M4A) into text using OpenAI's Whisper model.
The script should accept the input audio file path as a command-line argument, verify the file exists, load the "base" Whisper model, and transcribe the audio.
It should save the full transcribed text to an output file named "out.txt", and also print a preview of the transcription to the console, truncating it to the first 200 characters if the text is longer.
Include appropriate status messages during loading and processing, and handle the case of missing or incorrect command-line arguments with a usage message and graceful exit."""

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
