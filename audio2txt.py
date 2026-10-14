#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts an audio recording in M4A format into a plain-text transcript. The tool should accept an input audio file path and an optional output text file path (defaulting to a generic name such as "out.txt"). Before doing any work, it should verify that the input file exists and report a clear error and exit with a failure status if it does not. It should also warn, without stopping, if the file does not carry the expected M4A extension.
The script should convert the compressed M4A audio into an uncompressed intermediate format suitable for speech recognition, using a temporary file that is cleaned up after use. It should then load the converted audio, estimate and compensate for background noise before transcribing, and send the audio to a speech-to-text service to produce the recognized text. The transcript should be written to the specified output file, and the tool should print clear progress messages at each stage (processing, converting, loading, noise adjustment, transcribing, and saving).
Handle failures gracefully: if the speech service cannot understand the audio or cannot be reached, report a meaningful message to the user rather than crashing with a raw traceback. Ensure temporary files are removed even when an error occurs. The script should be runnable from the command line with the input file as a required argument and the output file as an optional argument, and it should print a confirmation with the output location when the transcription succeeds.
---"""

from __future__ import annotations
import os
import sys
import tempfile
from pydub import AudioSegment
import speech_recognition as sr


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
