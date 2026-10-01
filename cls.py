#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans all files in the current working directory (non-recursively, ignoring subdirectories) and, for each file, extracts a label from its filename stem: if the stem contains a hyphen, take the substring before the first hyphen, otherwise use the whole stem.
Collect these labels into a list preserving the order files were found via Path.glob("*").
Finally, print all collected labels on a single line separated by three spaces, with no trailing newline structure beyond the final print's default behavior."""

from pathlib import Path

if __name__ == "__main__":
    nl = []
    cwd = Path.cwd()
    for f in cwd.glob("*"):
        stm = f.stem
        if not f.is_file():
            continue
        if "-" in stm:
            indx = stm.index("-")
            nl.append(stm[:indx])
        else:
            nl.append(stm)
    for k in nl:
        print(k, end="   ")
