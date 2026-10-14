#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line batch optimizer for CSS files. It should accept one or more file paths as arguments; if no arguments are given, it should automatically discover all CSS files (including minified CSS files) in the current working directory. For each file, the script should skip any file that does not exist or that consists of only a single line, and otherwise run an external CSS minification/optimization tool at a high optimization level, configured to remove duplicate rules and disable unnecessary transformations. The script should print the file name as it processes each file, then report the outcome for that file: indicate "no change" when the optimized size equals the original, or report the number of bytes saved, a human-readable size reduction, and the resulting size as a percentage of the original when it shrank. If the optimizer fails, the script should report an error for that file and continue processing the remaining files. Use color-coded terminal output to distinguish success, no-change, and error states. Track the total size of the working directory before processing so the script can report overall space savings at the end. The script should be robust to missing files and tool failures, and should produce concise, readable console output suitable for batch use in build pipelines.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import cprint, fsz, get_files, gsz, mpf, runcmd


def process_file(path) -> bool:
    path = Path(path)
    before = gsz(path)
    if not path.exists():
        return False
    if len(path.read_text().splitlines()) == 1:
        return False
    print(f"{path.name}", end=" ")
    cmd = [
        "cleancss",
        "-O2",
        "all:off;removeDuplicateRules:on",
        str(path),
        "-o",
        str(path),
    ]
    res, _, _err = runcmd(cmd, show_output=True)
    if not res:
        after = gsz(path)
        diffsize = before - after
        if not diffsize:
            cprint("[NO CHANGE]", "white")
        if diffsize:
            ratio = after / before * 40
            cprint(f"[OK] - {fsz(diffsize)} {abs(ratio):.1f}%", "cyan")
        return True
    cprint("[ERROR]", "red")
    return False


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
