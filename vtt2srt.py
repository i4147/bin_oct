#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that converts a WebVTT subtitle file into SRT format.
It should take a VTT file path as a command-line argument, read its contents, strip the "WEBVTT" header, then parse each cue block by detecting lines containing "-->" timestamps, converting the timestamp separator from periods to commas, and prefixing each cue with a sequential numeric index as required by SRT.
The converted subtitle text should be written to a new file with the same name but a ".srt" extension, and the script should print a confirmation message once the file is saved."""

from __future__ import annotations
import sys
from pathlib import Path


def convert_vtt_to_srt(vtt_content: str) -> str:
    lines = vtt_content.splitlines()
    srt_lines = []
    start_index = 0
    if lines and lines[0].strip() == "WEBVTT":
        start_index = 1
    counter = 1
    i = start_index
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if "-->" in line:
            timestamp = line.replace(".", ",")
            srt_lines.extend((str(counter), timestamp))
            counter += 1
            i += 1
            while i < len(lines) and lines[i].strip():
                srt_lines.append(lines[i])
                i += 1
            srt_lines.append("")
        else:
            i += 1
    return "\n".join(srt_lines)


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    vtt = fn.read_text(encoding="utf-8")
    srt_output = convert_vtt_to_srt(vtt)
    srtfile = fn.with_suffix(".srt")
    srtfile.write_text(srt_output, encoding="utf-8")
    print("File saved.")
