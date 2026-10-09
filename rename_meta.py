#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that batch-processes metadata files by extracting package name and version information and saving renamed copies to a fixed output directory.
It should retrieve a list of input files using a helper function, read each file's second and third lines to parse "name:" and "version:" fields (case-insensitive), and then write the file's full content to a new file in "/data/data/com.termux/files/home/tmp/metadata" named using the pattern "name-version.metadata" or just "name.metadata" if the version is missing, avoiding overwrites by generating a unique path when a filename collision occurs.
It should print color-coded status messages (green for name+version success, yellow for name-only success, and another color for missing data or nonexistent files) using a custom print helper, and iterate over all files in the input source, returning True or False/None depending on whether processing succeeded for each file."""

from __future__ import annotations
from pathlib import Path
import sys

from dh import cprint, get_files, unique_path


OUT_PATH = Path("/data/data/com.termux/files/home/tmp/metadata")


def process_file(path: Path) -> bool | None:
    pkgname = ""
    path = Path(path)
    pkgversion = ""
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    line1 = lines[1]
    line2 = lines[2]
    striped1 = line1.lower().strip()
    striped2 = line2.lower().strip()
    if striped1.startswith("name:"):
        pkgname = striped1.replace("name:", "").lstrip()
    if striped2.startswith("version:"):
        pkgversion = striped2.replace("version:", "").lstrip()
    if pkgversion and pkgname:
        outfn = Path(pkgname + "-" + pkgversion + ".metadata")
        outpath = OUT_PATH / outfn
        if outpath.exists():
            outpath = unique_path(outpath)
        outpath.write_text(content, encoding="utf-8")
        cprint(f"{outfn} created.", "green")
    elif pkgname and (not pkgversion):
        outfn = Path(pkgname + ".metadata")
        outpath = OUT_PATH / outfn
        content = path.read_text(encoding="utf-8")
        if outpath.exists():
            outpath = unique_path(outpath)
        content = path.read_text(encoding="utf-8")
        outpath.write_text(content, encoding="utf-8")
        cprint(f"{outfn} created.", "yellow")
    elif not pkgname and (not pkgversion):
        cprint(f"no data{path}", "cyan")
        input("what u wanna do?")
    return None


def main() -> None:
    cwd = Path.cwd()
    for path in get_files(cwd):
        if path.is_file() and (path.name == "METADATA" or path.suffix == ".metadata"):
            process_file(path)


if __name__ == "__main__":
    raise SystemExit(main())
