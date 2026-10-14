#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a Midnight Commander command history file from a Termux environment, extands stored in its command-line section, removes duplicate entries, and appends the unique commands to a shell history file so they become available in the user's shell history.
The script should:
- Locate and read the source history file, which uses an INI-like layout where a designated section header marks the start of recorded commands, with each entry stored as a key-value pair.
- Capture only the entries within that section, stopping when a blank line or the end of the section is reached, and extract only the value portion of each entry while trimming surrounding whitespace.
- Eliminate duplicate commands so that each command appears only once in the output.
- Append the resulting unique commands to the target shell history file, preserving any existing content in that file, with each command written on its own line.
- Handle file encoding as UTF-8 for both reading and writing.
- Run as a standalone command-line utility that performs its task immediately when executed, without requiring user interaction.
- Use the Termux home directory paths shown as the default locations, while keeping those paths easy to adjust.
---"""

from __future__ import annotations
from pathlib import Path

if __name__ == "__main__":
    input_file = Path("/data/data/com.termux/files/home/.local/share/mc/history")
    output_file = Path("/data/data/com.termux/files/home/.bash_history")
    cmdline_section = []
    lines = input_file.read_text(encoding="utf8").splitlines()
    capture = False
    for line in lines:
        line = line.strip()
        if line == "[cmdline]":
            capture = True
            continue
        if capture:
            if line == "":
                break
            cleaned_line = line.split("=", 1)[-1].strip()
            cmdline_section.append(cleaned_line)
    soniq = list(set(cmdline_section))
    with output_file.open("a", encoding="utf-8") as file:
        file.writelines(cmd + "\n" for cmd in soniq)
