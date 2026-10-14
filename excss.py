#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a set of local HTML files, extracts the inline CSS embedded in each page's style blocks, and saves each extracted stylesheet as a separate standalone CSS file in a designated output folder.
The script should accept one or more HTML file paths (or a directory to scan for HTML files) as input from the command line. For each HTML file, it should read the content using UTF-8 encoding, locate every embedded style block, and report how many were found. Each non-empty style block should be written to its own uniquely named CSS file inside the output folder, creating that folder if it does not exist. Empty or near-empty style blocks should be skipped. The script must never overwrite an existing file; if a generated filename collides with an existing one, it should produce a new unique name instead. Use UTF-8 encoding for all written files.
Provide clear, color-coded or otherwise visually distinct console messages to indicate progress, the number of styles found per file, successful file creation, and any collisions or errors. The script should handle missing files, unreadable files, and malformed HTML gracefully, continuing to process remaining files rather than crashing. At the end, print a summary of how many HTML files were processed, how many style blocks were extracted, and how many CSS files were created.
Include a main entry point that parses command-line arguments, validates inputs, and orchestrates the processing. Ensure the script is well-structured, readable, and includes brief docstrings explaining its purpose and usage.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from typing import TYPE_CHECKING
from bs4 import BeautifulSoup
from dh import cprint, get_files, get_random_filename, mpf

if TYPE_CHECKING:
    from bs4.element import PageElement


def save_style(str1: list[PageElement]) -> None:
    if not str1 or len(str(str1)) < 2:
        return
    fn = "css/"
    fn += get_random_filename(10)
    fn += ".css"
    path = Path(fn)
    if path.exists():
        cprint(f"[{fn}] exists.", "red")
        path = unique_path(path)
    path.write_text("\n".join(list(str1)), encoding="utf-8")
    cprint(f"{[fn]} created.", "cyan")
    return


def process_file(path) -> bool:
    path = Path(path)
    html_content = path.read_text(encoding="utf-8")
    path = Path(path)
    soup = BeautifulSoup(html_content, "html.parser")
    styles = soup.find_all("style")
    if styles:
        cprint(f"{[path.name]} : {len(styles)} styles found.", "green")
        for style in styles:
            save_style(style.contents)
    return True


def main() -> None:
    outpath = Path("css")
    if not outpath.exists():
        outpath.mkdir(exist_ok=True)
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(arg) for arg in args] if args else get_files(cwd, ext=[".html", ".htm"])
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
