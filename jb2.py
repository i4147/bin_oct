#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that recursively finds all JSON files in the current working directory, reformats each one by parsing it and rewriting it with indent=2 and ensure_ascii=False (effectively pretty-printing/normalizing it), and processes the files in parallel using a helper multiprocessing function.
For each file it should print the filename along with the file size change (before vs after) as a colored percentage, skip or report unchanged/empty files, and catch and report JSON parse errors in a distinct color.
At the end it should print the total directory size change before and after processing, and exit with status code 1 if no JSON files were found or if the total size did not change."""

import json
import sys
from pathlib import Path
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
