#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that cleans up the user's bash history file located at ~/.bash_history.
The script should read all lines from the file, filter out any lines containing the substring 'cd "`printf', then deduplicate the remaining lines using a set, and finally overwrite the original file with the resulting unique lines.
After completing the operation, it should print "done." to indicate success."""

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
