#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that removes all lines containing a given search string from one or more text files.
It should accept command-line arguments where the last argument is the search string and any preceding arguments are file paths; if no file paths are given, it should automatically gather non-binary files from the current directory using a helper module named "dh" (which provides get_nobinary, gsz, and fsz functions).
The script must read each file as UTF-8 (ignoring decode errors), filter out lines containing the search string, and overwrite the file only if its content changed, tracking and reporting the number of removed lines per file.
For a single file it should process it directly, but for multiple files it should use a multiprocessing Pool with 8 workers to clean them in parallel, and it should also compute the total size of files in the working directory before and/or after processing.
"""

from __future__ import annotations
import sys
from multiprocessing import Pool
from pathlib import Path
from dh import fsz, get_nobinary, gsz


def clean_text(text, strtofind):
    kept = []
    removed = 0
    for line in text.splitlines():
        if any(s in line for s in strtofind):
            removed += 1
        else:
            kept.append(line)
    return "\n".join(kept), removed


def clean_file(path, strtofind):
    try:
        original = Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return path, 0, 0
    cleaned, removed = clean_text(original, strtofind)
    if cleaned != original:
        Path(path).write_text(cleaned, encoding="utf-8")
    return path, removed, len(original) - len(cleaned)


def main():
    args = sys.argv[1:]
    if not args:
        print(f"usage: {sys.argv[0]} [file ...] <search_string>")
        return 1
    strtofind = [args[-1]]
    file_args = args[:-1]
    files = [Path(a) for a in file_args] if file_args else get_nobinary(Path.cwd())
    root = Path.cwd()
    isz = gsz(root)
    total_removed = 0
    if len(files) == 1:
        path, removed, _ = clean_file(files[0], strtofind)
        total_removed += removed
        print(f"{path}: {removed} line(s) removed")
    else:
        pool = Pool(8)
        results = [pool.apply_async(clean_file, (f, strtofind)) for f in files]
        pool.close()
        pool.join()
        for r in results:
            path, removed, _ = r.get()
            if removed:
                print(f"{path}: {removed} line(s) removed")
            total_removed += removed
    esz = gsz(root)
    print(f"total lines removed : {total_removed}")
    print(f"space freed : {fsz(isz - esz)}")
    return None


if __name__ == "__main__":
    raise SystemExit(main())
