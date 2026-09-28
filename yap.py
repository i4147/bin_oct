#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python CLI script that recursively finds Python (.py) files in a given directory (via a helper get_pyfiles from a local "dh" module) and reformats/cleans each file's source code in place using a selectable code-formatting backend controlled by a MODE constant or CLI argument, supporting "autoflake" (remove unused imports), "isort" (sort imports), "black" (format with target Python versions 3.10/3.13 and 120 line length), "autopep8" (aggressive PEP8 fixes), and "yapf" as interchangeable modes.
It should use argparse to accept options such as target directory/files and formatting mode, read each file's original text, apply the chosen formatter's transformation function to produce new code, and write the result back to disk, while tracking each file's before/after size in bytes and processing time using perf_counter.
It should leverage utility functions from the "dh" module (cprint for colored console output, format_time and fsz for human-readable time/size formatting, and mpf, presumably for multiprocessing/parallel file handling) to report progress and results, such as filenames, size changes, and elapsed time, for each processed file and likely a final summary across all files."""

import argparse
from pathlib import Path
from time import perf_counter as pff
from typing import Any
from dh import cprint, format_time, fsz, get_pyfiles, mpf

MODE: str = "black"
CHUNK_SIZE: Any = 1024 * 1024


def process_file(path: str | Path, mode: str = MODE):
    stime = pff()
    path = Path(path)
    before: int = path.stat().st_size
    after: int = before
    try:
        original_code: str = path.read_text(encoding="utf-8")
        code = original_code
        match mode:
            case "autoflake":
                from autoflake import fix_code as fix_with_autoflake

                code = fix_with_autoflake(original_code, remove_all_unused_imports=True)
            case "isort":
                from isort import code as fix_with_isort

                code = fix_with_isort(original_code)
            case "black":
                from black import Mode as _Mode
                from black import TargetVersion as _tv
                from black import format_str

                code = format_str(
                    original_code,
                    mode=_Mode(target_versions={_tv.PY310, _tv.PY313}, line_length=120),
                )
            case "autopep":
                from autopep8 import fix_code as fix_with_autopep

                code = fix_with_autopep(original_code, options={"aggressive": 2})
            case "yapf":
                from yapf.yapflib.yapf_api import FormatCode as fix_with_yapf

                code, _ = fix_with_yapf(original_code)
            case _:
                from black import Mode as _Mode
                from black import TargetVersion as _tv
                from black import format_str

                code = format_str(
                    original_code,
                    mode=_Mode(target_versions={_tv.PY310, _tv.PY313}, line_length=120),
                )
        after = len(code)
        dsz = abs(before - after)
        etime = pff()
        if dsz:
            path.write_text(code, encoding="utf-8")
            ratio = dsz / before * 40
            cprint(
                f"({format_time(etime - stime)}) | {fsz(dsz)} | {ratio:.1f}%", "cyan"
            )
            return True
        print(f"{path.name} ", end=" ")
        cprint(f"({format_time(etime - stime)}) | (no change)", "grey")
        return True
    except Exception as e:
        cprint("[ERROR]", "red", end=" ")
        print(f"{path.name}: {e}")
        return False


def main() -> None:
    global MODE
    p = argparse.ArgumentParser(
        description="Fast Python API-based formatter (Lazy Loading)"
    )
    p.add_argument("-b", "--black", action="store_true", help="Use black style")
    p.add_argument("-a", "--autopep", action="store_true", help="Use autopep8 style")
    p.add_argument("-i", "--isort", action="store_true", help="Sort imports")
    p.add_argument("-r", "--raui", action="store_true", help="Autoflake cleanup")
    p.add_argument("-y", "--yapf", action="store_true", help="yapf formatter")
    args = p.parse_args()
    cwd = Path.cwd()
    files = get_pyfiles(cwd)
    if args.raui:
        MODE = "autoflake"
    elif args.black:
        MODE = "black"
    elif args.autopep:
        MODE = "autopep"
    elif args.isort:
        MODE = "isort"
    elif args.yapf:
        MODE = "yapf"
    else:
        MODE = "black"
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
