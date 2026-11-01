#!/data/data/com.termux/files/usr/bin/env python
"""mchist.py -- copy the Midnight Commander history into ``.bash_history``.

The command lines recorded by ``mc`` are appended to the shell history.
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
