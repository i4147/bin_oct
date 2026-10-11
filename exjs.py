#!/data/data/com.termux/files/usr/bin/env python
"""Write a single self-contained Python script that extracts inline JavaScript from HTML files and saves each script block as its own `.js` file. Describe it as follows so it can be rebuilt from scratch.

**Purpose:** A command-line utility that scans HTML files, finds every `<script>` element, and writes the contents of each one to a separate JavaScript file under a `js/` directory with a randomly generated name.

**Shebang and imports:** Start with a Termux-style shebang pointing to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/env python`. Use `from __future__ import annotations`. Import `sys`, `Path` from `pathlib`, `TYPE_CHECKING` from `typing`, and `BeautifulSoup` from `bs4`. Under a `TYPE_CHECKING` guard, import `PageElement` from `bs4.element` for type hints only. From a local helper module named `dh`, import `cprint` (colored console printing), `get_files` (directory file lookup filtered by extension), `get_random_filename` (generates a random name of a given length), and `mpf` (runs a function over a list of files, presumably in parallel).

**Constants:** Define `MAX_QUEUE = 16` at module level. It is defined but not used by the logic, so it can be kept for parity.

**Function `save_script(str1)`:** Takes a list of page elements (the `.contents` of a script tag). Build the target path as `js/` plus a random 10-character name plus `.js`, wrapped in a `Path`. If that file already exists, print a red message saying it exists and return `False`. Otherwise write the elements joined by newlines to the file using UTF-8 encoding, print a cyan confirmation showing the path, and return `True`. Note that the join iterates over the element list directly; the elements are expected to be strings (NavigableString), so reproduce that behavior as-is.

**Function `process_file(path)`:** Accept a path (string or Path). Convert it to `Path`, read the file as UTF-8 text, and parse it with BeautifulSoup using the `html.parser` backend. Find all `script` tags. If any are found, print a magenta message giving the file's name and the count, then call `save_script` on each script's `.contents`. Always return `True`. Re-converting the path to `Path` twice is harmless redundancy and may be kept.

**Function `main()`:** Ensure a `js` directory exists in the current working directory, creating it if missing. Get the current working directory. Read command-line arguments excluding the program name. If arguments were given, convert each to a `Path`; otherwise call `get_files` on the cwd with extensions `.html` and `htm`. Note the second extension is missing its leading dot, so reproduce it exactly as written. Pass the resulting file list and `process_file` to `mpf`.

**Entry point:** Under the standard `__main__` guard, call `main()` and pass its result to `raise SystemExit`, so the script exits with a normal status.

**Behavior and edge cases to preserve:**
- Output directory is relative to the current working directory, not to the input file.
- Duplicate random names are skipped rather than overwritten; a collision prints a message and does not raise.
- Files are read with UTF-8; no explicit error handling is present, so unreadable or non-UTF-8 files will raise exceptions.
- HTML files with no script tags produce no output and no message.
- Script files are written without any header or metadata, one per script block, with contents joined by newline characters.
- Console output uses colors via `cprint`: red for collisions, cyan for created files, magenta for per-file script counts.

**Dependencies:** `beautifulsoup4` and a local `dh` helper module providing the four named functions. The script targets Termux on Android.

**Usage:** Run from a directory containing HTML files with no arguments to process all `.html`/`htm` files found there, or pass one or more file paths as arguments to process only those files. Extracted scripts appear in `js/` under the working directory.
---"""

from __future__ import annotations

import sys
from pathlib import Path
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
