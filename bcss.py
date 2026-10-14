#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a batch CSS formatter. It should accept one or more CSS file paths from the command line; if none are given, it should automatically find all CSS files in the current working directory (including minified CSS files). For each file, it should reformat the CSS into a beautified, human-readable layout by invoking an external CSS beautification tool, overwriting the file in place. The script should process multiple files in parallel for speed, and report per-file progress with the file name and the outcome: whether the file was successfully beautified and how many bytes were saved or added (with a percentage change), reported as "no change" if nothing differed, or flagged as an error if the external tool failed. Missing files should be skipped gracefully. Output should use colored console messages to distinguish success, no-change, and error states. After processing, the script should display the total size difference across the working directory, showing the overall space change in human-readable units. The script should be robust, avoid crashing on individual file failures, and keep the console output concise and easy to scan.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import cprint, fsz, get_files, gsz, mpf, runcmd


def process_file(path) -> bool | None:
    path = Path(path)
    before = gsz(path)
    if not path.exists():
        return False
    print(f"{path.name}", end=" ")
    cmd = ["cleancss", "--format", "beautify", str(path), "-o", str(path)]
    res, _, _err = runcmd(cmd, show_output=True)
    if not res:
        after = gsz(path)
        diffsize = before - after
        if not diffsize:
            cprint("[NO CHANGE]", "white")
            return None
        if diffsize:
            ratio = diffsize / before * 40
            cprint(f"[OK] - {fsz(diffsize)} {abs(ratio):.1f}%", "cyan")
        return None
    cprint("[ERROR]", "red")
    return None


def main() -> None:
    args = sys.argv[1:]
    cwd = Path.cwd()
    before = gsz(cwd)
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".css", ".min.css"])
    _ = mpf(process_file, files)
    diff_size = before - gsz(cwd)
    cprint(f"space freed : {fsz(diff_size)}", "green")


if __name__ == "__main__":
    raise SystemExit(main())
