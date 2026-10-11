#!/data/data/com.termux/files/usr/bin/env python
"""You are writing a single self-contained prompt that will instruct an AI coding agent to recreate a Python command-line script from scratch. Write the prompt so the agent can build the script without seeing any original code. Do not include code, code snippets, or identifiers that read as code. Describe behavior in plain language.

Create a Python 3 command-line tool that converts HTML files into Markdown and optionally deletes the original HTML files. It is intended to run under Termux on Android, so the shebang line should point to Termux's Python at /data/data/com.termux/files/usr/bin/env python.

**Dependencies and imports**
- Use the `from __future__ import annotations` feature for type hints.
- Use the standard library modules for system arguments and path handling.
- Use the third-party `html2text` package for HTML-to-Markdown conversion.
- Use the third-party `readability` package (the Python port of Mozilla Readability) to extract the main article content from a page.
- Import two helpers from a local module named `dh`: a function `get_files` for recursively finding files by extension, and a function `mpf` whose role is not needed for the core logic; import it to match the original, but the script does not depend on its output.

**Global configuration**
- A module-level boolean flag `remove_orig` set to true, controlling whether the original HTML file is deleted after successful conversion.

**Core function: process_file(path)**
- Accepts a string or Path. Convert it to a Path.
- Compute the output path by replacing the file's suffix with `.md` in the same directory.
- If the Markdown output file already exists, return immediately with that output path and a success flag of true, without reprocessing. Do not print anything in this case.
- Otherwise, inside a try block:
  - Read the file as UTF-8 text, ignoring decoding errors.
  - Pass the HTML to a readability `Document`, and call its summary method to get the main article HTML.
  - Create an `html2text.HTML2Text` instance configured as follows: keep links, keep images, keep tables, and disable line wrapping (body width zero).
  - Convert the summary HTML to Markdown with that instance.
  - If the resulting Markdown is non-empty after stripping whitespace:
    - Write it to the `.md` file as UTF-8.
    - Print a success line in the form of a check mark, then "Converted:", the original file's name, an arrow, and the new Markdown file name.
    - If the removal flag is enabled, delete the original file.
    - Return the Markdown path and true.
  - If the Markdown is empty or whitespace only:
    - Print a cross mark followed by "No content extracted from" and the original file name.
    - Return the original path and false. Do not delete the file.
- Any exception in the try block is caught generically: print a cross mark followed by "Error:" and the exception message, then return the original path and false.
- Return type is a tuple of a Path and a boolean.

**Main entry point (when run as a script)**
- Get the current working directory.
- Take command-line arguments after the script name.
- If arguments are provided, treat each as a file path, converting each to a Path.
- If no arguments are given, recursively find files in the current directory with extensions `.html`, `.htm`, `.xhtml`, and `.xhtm` using the `get_files` helper with those extensions.
- Count the resulting files.
- If exactly one file is found, call the processing function on it.
- Note for implementation: the original script contains an incomplete branch here. Implement the intended behavior by also handling the multiple-file case: loop over all files, call the processing function on each, and print a summary line stating how many files were processed. For zero files, print a message saying no HTML files were found in the current directory and exit cleanly.
- Use a conventional structure with a `main` guard.

**Edge cases and behavior notes**
- Existing Markdown outputs are skipped, making the tool idempotent.
- Non-UTF-8 bytes are ignored rather than causing failure.
- Files that yield no extractable content are left untouched.
- Deletion of originals occurs only after a Markdown file is successfully written.
- Errors on individual files should not stop processing of the remaining files.
- Output uses Unicode symbols for status, so the script must write to a UTF-8 capable terminal.

**Usage**
- Run with no arguments to convert all HTML files found recursively under the current directory.
- Run with one or more file paths to convert only those files.

Deliver the complete script as a single file, with clear comments only where logic is non-obvious, matching a concise, pragmatic style.
---"""

from __future__ import annotations

import sys
from pathlib import Path

import html2text
from dh import get_files, mpf
from readability import Document

remove_orig = True


def process_file(path: str | Path) -> tuple[Path, bool]:
    path = Path(path)
    md_file = path.with_suffix(".md")
    if md_file.exists():
        return (md_file, True)
    try:
        html_content = path.read_text(encoding="utf-8", errors="ignore")
        doc = Document(html_content)
        main_content = doc.summary()
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_tables = False
        h.body_width = 0
        markdown = h.handle(main_content)
        if markdown and markdown.strip():
            md_file.write_text(markdown, encoding="utf-8")
            print(f"✓ Converted: {path.name} -> {md_file.name}")
            if remove_orig:
                path.unlink()
            return (md_file, True)
        print(f"✗ No content extracted from {path.name}")
        return (path, False)
    except Exception as e:
        print(f"✗ Error: {e}")
        return (path, False)


if __name__ == "__main__":
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".html", ".htm", ".xhtml", ".xhtm"])
    numf = len(files)
    if numf == 1:
        process_file(files[0])
        sys.exit(0)
    mpf(process_file, files)
