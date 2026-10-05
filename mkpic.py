#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that recursively finds and compiles .py files into bytecode (.pyc) using the compileall module, relying on a helper module "dh" (with get_pyfiles and mpf) to enumerate target Python files.
It should accept command-line arguments to control optimization level (0, 1, or 2 via -o/--optimize), whether to use legacy pyc placement (removing/replacing any old-style .pyc next to the source), and whether to delete the original .py source file after successful compilation.
The script should skip symlinks, nonexistent paths, and anything under a .git directory, recurse into directories to process all contained .py files, and set the PYTHONPYCACHEPREFIX environment variable to "__pycache__" before processing, printing an error and returning a nonzero status if an invalid optimize level is supplied."""

from __future__ import annotations
import compileall
import os
import sys
from pathlib import Path
from dh import get_pyfiles, mpf

REMOVE_ORIG = False
LEGACY_MODE = False
OPTIMIZE_LEVEL = 0


def process_file(path) -> bool | None:
    path = Path(path)
    if not path.exists() or path.is_symlink():
        return False
    if ".git" in path.parts:
        return False
    if path.is_dir():
        for f in path.rglob("*.py"):
            process_file(f)
    if path.is_file():
        pyc_file = path.with_suffix(".pyc") if LEGACY_MODE else None
        if pyc_file and pyc_file.exists():
            pyc_file.unlink()
        compileall.compile_file(path, optimize=OPTIMIZE_LEVEL, legacy=LEGACY_MODE)
        if REMOVE_ORIG:
            path.unlink()
        return True
    return False


def main():
    global REMOVE_ORIG, LEGACY_MODE, OPTIMIZE_LEVEL
    os.environ["PYTHONPYCACHEPREFIX"] = "__pycache__"
    cwd = Path.cwd()
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-o", "--optimize"):
            if i + 1 < len(args):
                try:
                    OPTIMIZE_LEVEL = int(args[i + 1])
                    if OPTIMIZE_LEVEL not in (0, 1, 2):
                        print(f"Error: Optimize level must be 0, 1, or 2 (got {OPTIMIZE_LEVEL})")
                        return 1
                    i += 2
                    continue
                except ValueError:
                    print(f"Error: Invalid optimize level: {args[i + 1]}")
                    return 1
            else:
                print("Error: -o/--optimize requires an argument (0, 1, or 2)")
                return 1
        elif arg in ("-l", "--legacy"):
            LEGACY_MODE = True
            i += 1
        elif arg in ("-h", "--help"):
            print("Usage: python script.py [options] [files/directories]")
            print("Options:")
            print("  -o, --optimize LEVEL  Set optimization level (0, 1, or 2, default: 0)")
            print("  -l, --legacy        Create legacy .pyc file beside original file")
            print("  -h, --help          Show this help message")
            print("  files/directories   Files or directories to process (default: current directory)")
            return 0
        else:
            break
    files = []
    if i < len(args):
        for arg in args[i:]:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(get_pyfiles(p))
    else:
        files = get_pyfiles(cwd)
    if not files:
        print("No Python files found to process")
        return 0
    if len(files) == 1:
        process_file(files[0])
        return 0
    mpf(process_file, files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
