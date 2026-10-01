#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python CLI script that beautifies and reformats CSS files in place using the "cleancss" command-line tool.
It should accept specific file paths as command-line arguments, or if none are given, automatically discover all .css and .min.css files in the current directory.
For each file, it records the size before and after processing, prints per-file status (no change, success with bytes saved and percentage reduction, or error) using colored console output, and processes files in parallel via a multiprocessing helper.
Finally, it reports the total disk space freed across all processed files."""

import sys
from pathlib import Path
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
            return
        if diffsize:
            ratio = diffsize / before * 40
            cprint(f"[OK] - {fsz(diffsize)} {abs(ratio):.1f}%", "cyan")
        return
    cprint("[ERROR]", "red")
    return


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
