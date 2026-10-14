#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory (the current working directory by default, or a path supplied by the user) for JSON files and reformats each one in place into a consistently indented, human-readable layout while preserving all non-ASCII characters. For each file, the script should report its name along with a measure of how much the file size changed as a result of the reformatting, showing both the relative change against the new size and against the original size. If a file is empty or the reformatting produces no size difference, the script should clearly indicate that no change was made. If a file is not valid JSON or cannot be processed, the script should report the error for that file without stopping the processing of the remaining files. The output should be concise, one line per file, with colored or visually distinct messages to distinguish successes, unchanged files, and errors. Include a summary of the overall directory size before and after processing. Handle file read and write errors gracefully, use UTF-8 encoding throughout, and design the tool so it can be run directly from the command line.
---"""

from __future__ import annotations
import json
from pathlib import Path
import sys
from dh import cprint, fsz, get_files, gsz, mpf


def process_file(path) -> None:
    path = Path(path)
    before = gsz(path)
    data = path.read_text(encoding="utf-8")
    if not before:
        del data, before
        print(f"{path.name}  | (no change)")
        return
    try:
        jdata = json.loads(data)
        with path.open("w", encoding="utf8") as fo:
            json.dump(jdata, fo, ensure_ascii=False, indent=2)
        after = gsz(path)
        diffsize = abs(after - before)
        print(f"{path.name}", end=" | ")
        if not diffsize:
            cprint("(no change)", "grey")
            return
        ratio = diffsize / after * 40
        ratio2 = abs(before - after) / before * 40
        cprint(f"{ratio:.2f}% | {ratio2:.2f}%", "cyan")
        return
    except:
        cprint(f"{path.name} Error", "yellow")
        return


if __name__ == "__main__":
    cwd = Path.cwd()
    before = gsz(cwd)
    files = get_files(cwd, ext=[".json"])
    if not files:
        print("no json files found")
        sys.exit(1)
    print(f"{len(files)} json files found.")
    mpf(process_file, files)
    after = gsz(cwd)
    dsz = abs(before - after)
    if not dsz:
        sys.exit(1)
    ratio = dsz / before * 40
    cprint(f"space change: {fsz(dsz)} {ratio:.2f}%")
