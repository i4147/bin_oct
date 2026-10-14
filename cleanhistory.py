#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans up the user's shell command history file located in the user's home directory (the standard Bash history file). The script should read every line of the history file, discard any line containing the specific junk pattern `cd "`printf` (a stray command fragment that pollutes the history), remove duplicate lines so that each unique command appears only once, and then overwrite the original history file with the filtered result. The file should be read and written using UTF-8 encoding. The order of the remaining lines does not need to be preserved. When the operation completes, the script should print a short confirmation message indicating it is done. The script should run as a standalone command-line tool that performs its work automatically when executed directly, without requiring any user-supplied arguments.
---"""

from __future__ import annotations
from pathlib import Path

if __name__ == "__main__":
    fn = Path.home() / ".bash_history"
    nl = []
    with fn.open(encoding="utf-8") as f:
        nl.extend(line for line in f if 'cd "`printf' not in line)
    nl = list(set(nl))
    with fn.open("w", encoding="utf-8") as fo:
        fo.writelines(nl)
    print("done.")
