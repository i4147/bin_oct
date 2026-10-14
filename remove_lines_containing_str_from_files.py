#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line text-cleaning utility for files. It takes one or more file paths and a search string as arguments, where the search string is always the final argument. For each specified file, it reads the content as text (tolerating invalid or non-UTF-8 bytes), removes every line that contains the search string, and saves the file back in place only when something was actually removed. Lines that do not match must be preserved in their original order. The tool should report, for each processed file, how many lines were removed and how many characters were eliminated. If files are not explicitly given, the script should fall back to processing a sensible default set of files, such as all non-binary files discovered in the current working directory tree, skipping binary content. If the script is invoked without any arguments, it should print a brief usage message showing the expected syntax and exit with a non-zero status. Files that cannot be read should be skipped gracefully without stopping the overall run. The work across multiple files should be parallelized to speed up processing of large sets of files, with the results aggregated and summarized at the end. The overall behavior must be safe, predictable, and accurate, never altering files that contain no matching lines.
---"""

from __future__ import annotations
from multiprocessing import Pool
from pathlib import Path
import sys
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
