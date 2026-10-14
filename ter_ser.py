#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a target directory (or the current working directory when none is given) for JavaScript source files with the extensions .js, .jsx, .jsm, and .jsc, and minifies each one in place using the Terser command-line minifier with compression and name mangling enabled. The script should accept one or more file or directory paths as command-line arguments, expanding directories into the JavaScript files they contain.
Behavior requirements:
- Skip any file already named with a ".min.js" suffix so that previously minified outputs are not reprocessed.
- Skip files located inside a notebook-related site-packages directory.
- Skip files that do not exist, are empty, or consist of only a single line, since they are assumed to be already minified.
- Invoke the external minifier safely: if it fails, report the error message to standard error and leave the original file untouched.
- On success, overwrite the original file with the minified output, UTF-8 encoded, and report the size reduction (original size versus new size, and the percentage saved) for each processed file, along with a final summary of how many files were processed and the total bytes saved.
- Handle missing arguments, invalid paths, and missing Terser installation gracefully with clear, user-friendly messages and a non-zero exit code on fatal errors.
- Print progress information so the user can follow which file is being processed.
The script should be runnable from the command line, be robust against individual file failures without aborting the whole batch, and produce a concise, readable console report.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import get_files, gsz, mpf, rrs, runcmd

EXT = [".js", ".jsx", ".jsm", ".jsc"]


def safe_run(path: Path) -> bool:
    cmd = ["terser", "--compress", "--mangle", "--", str(path)]
    res, txt, err = runcmd(cmd, show_output=False)
    if res != 0:
        print(f"Error running terser: {err}", file=sys.stderr)
        return False
    path.write_text(txt, encoding="utf8")
    return True


def process_file(path):
    path = Path(path)
    if path.name.endswith(".min.js"):
        return
    if "site-packages" in path.parts and "notebook" in path.parts:
        return
    before = gsz(path)
    if not path.exists() or not before:
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) == 1:
        del lines, before
        return
    if safe_run(path):
        after = gsz(path)
        rrs(path, before, after)
    return


def main():
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = []
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(get_files(p), ext=EXT)
    else:
        files = get_files(cwd, ext=EXT)
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
