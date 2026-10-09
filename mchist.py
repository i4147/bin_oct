#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that reads the Midnight Commander history file located at /data/data/com.termux/files/home/.local/share/mc/history, locates the "[cmdline]" section, and extracts each command line entry by stripping any leading "key=" prefix before the "=" sign.
The script should deduplicate the collected commands using a set, then append each unique command as a new line to the bash history file at /data/data/com.termux/files/home/.bash_history, creating the file if it does not exist.
It should stop parsing the cmdline section once it encounters an empty line, and all file operations should use UTF-8 encoding.
"""

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
