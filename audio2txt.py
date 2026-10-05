#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that converts an M4A audio file into text via speech recognition.
It should accept an input .m4a file path and an optional output text file path (default "out.txt"), validate that the input file exists and warn if it lacks the .m4a extension, then use pydub to convert the audio into a temporary WAV file.
Using the speech_recognition library, it should load the WAV file, adjust for ambient noise, transcribe the audio with Google's speech recognition API, and write the resulting text to the output file, printing progress messages at each step (conversion, loading, noise adjustment, transcription) along with a preview of the transcribed text (truncated to 200 characters if longer).
The script should handle missing input files by printing an error and exiting, and should clean up the temporary WAV file after processing."""

from __future__ import annotations
import os
import sys
import tempfile
import speech_recognition as sr
from pydub import AudioSegment


def m4a_to_text(input_file, output_file="out.txt"):
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    if not input_file.lower().endswith(".m4a"):
        print("Warning: Input file doesn't have .m4a extension. Continuing anyway...")
    print(f"Processing: {input_file}")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav_path = temp_wav.name
    try:
        print("Converting M4A to WAV...")
        audio = AudioSegment.from_file(input_file, format="m4a")
        audio.export(temp_wav_path, format="wav")
        recognizer = sr.Recognizer()
        print("Loading audio file...")
        with sr.AudioFile(temp_wav_path) as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio_data = recognizer.record(source)
        print("Transcribing audio to text...")
        try:
            text = recognizer.recognize_google(audio_data)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"✓ Transcription saved to: {output_file}")
            print(f"Transcribed text:\n{text[:200]}..." if len(text) > 200 else f"Transcribed text:\n{text}")
        except sr.UnknownValueError:
            print("Error: Speech recognition could not understand the audio")
            sys.exit(1)
        except sr.RequestError as e:
            print(f"Error: Could not request results from speech recognition service; {e}")
            sys.exit(1)
    finally:
        if os.path.exists(temp_wav_path):
            os.unlink(temp_wav_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python m4a_to_text.py <input_file.m4a>")
        print("Example: python m4a_to_text.py recording.m4a")
        sys.exit(1)
    input_file = sys.argv[1]
    m4a_to_text(input_file)
