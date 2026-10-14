#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory of HTML files, extracts the contents of every inline script block from each page, and saves each script's contents as a separate standalone JavaScript file in an output folder. The script should accept a source directory (or individual HTML file paths) from the command line, locate all HTML files to process, parse each page robustly, and report progress to the console with clear, color-coded status messages indicating which files were processed, how many script blocks were found, and which output files were created or skipped. Each output file should receive a unique, randomly generated name so that existing files are never overwritten; if a generated name collides with an existing file, the script should detect this and handle it gracefully. The script should create the output directory if it does not already exist, write all extracted content using UTF-8 encoding, and cap the number of concurrently queued or pending extraction tasks at a configurable maximum (default 16). It should handle missing files, unreadable files, and malformed HTML without crashing, continuing to process remaining files and summarizing totals (files processed, scripts extracted, errors encountered) when finished. Include a clear usage message when invoked without the required arguments, and keep the overall design simple, readable, and dependency-light.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from typing import TYPE_CHECKING
from bs4 import BeautifulSoup
from dh import cprint, get_files, get_random_filename, mpf

if TYPE_CHECKING:
    from bs4.element import PageElement
MAX_QUEUE = 16


def save_script(str1: list[PageElement]) -> bool:
    fn = "js/"
    fn += get_random_filename(10)
    fn += ".js"
    fn = Path(fn)
    if fn.exists():
        cprint(f"[{fn}] exists.", "red")
        return False
    if not fn.exists():
        fn.write_text("\n".join(list(str1)), encoding="utf-8")
        cprint(f"{[fn]} created.", "cyan")
    return True


def process_file(path) -> bool:
    path = Path(path)
    html_content = path.read_text(encoding="utf-8")
    path = Path(path)
    soup = BeautifulSoup(html_content, "html.parser")
    scripts = soup.find_all("script")
    if scripts:
        cprint(f"{[path.name]} : {len(scripts)} scripts found.", "magenta")
        for script in scripts:
            save_script(script.contents)
    return True


def main() -> None:
    if not Path("js").exists():
        Path("js").mkdir()
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(f) for f in args] if args else get_files(cwd, ext=[".html", "htm"])
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
