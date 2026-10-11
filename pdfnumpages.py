#!/data/data/com.termux/files/usr/bin/python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with the following specification:

Create a Python script (Termux-targeted, shebang pointing to the Termux Python interpreter) that renames PDF files in the current directory tree so each filename carries its page count.

**Purpose:** Recursively scan the current working directory and all subdirectories for `.pdf` files, determine each file's page count, and rename each file by appending the page count to its stem (e.g., `report.pdf` with 12 pages becomes `report12.pdf`), placed in the same directory.

**Dependencies and backend selection:**
- Prefer the `pymupdf` library for page counting. Import it inside a `try` block; if the import fails, set a flag indicating PyMuPDF is unavailable and fall back to `pdfplumber` (import it in the `except` branch).
- Page counting with PyMuPDF opens the document as a context manager and reads its page count. With pdfplumber, open the file as a context manager and count its pages.
- Use `from __future__ import annotations` and standard type hints throughout (`list[Path]`, `Iterator[str]`, `-> None`, etc.).

**Helper functions:**
1. `walk_files(directory)` — a generator that uses `os.walk` and yields full joined paths of every regular file under the directory, across all subdirectories.
2. `_page_count(path)` — takes a `Path` and returns the integer page count using the selected backend.
3. `process_file(path)` — takes a path string and performs the rename:
   - Convert to `Path`. Proceed only if the path exists and is not a symbolic link; otherwise do nothing.
   - Compute the page count, build the new name as `stem + str(pagecount) + ".pdf"`, and print the new name.
   - Build the target path in the same parent directory.
   - If the page count string already appears in the stem, return without renaming (this prevents repeated renaming of already-processed files).
   - If the target does not exist, rename the file and print `oldname --> newname`. If the target already exists, print that the new name exists and skip it.
   - Return nothing.

**Main flow:**
- Walk `"."` with `walk_files`, keep only entries that are regular files with the `.pdf` suffix (case-sensitive), and collect them as `Path` objects in a list.
- Process the collected files in parallel using a multiprocessing pool created with the `spawn` start method (via `get_context("spawn")`) with 8 worker processes, mapping `process_file` over the file paths. Use the pool as a context manager so it is closed and joined properly. Ensure the processing is guarded by an `if __name__ == "__main__":` block that calls `main()`, which is required for spawn-based multiprocessing.
- Pass string paths to workers (convert `Path` objects to `str` if needed for pickling compatibility).

**Output behavior:**
- Print the new filename for each processed file, then the rename message, or the "exists" message when the target is occupied.
- Print nothing else beyond these messages.

**Edge cases and error handling:**
- Skip symbolic links and non-existent paths silently.
- Skip files whose stem already contains the page count (idempotent re-runs).
- Do not overwrite existing files; report a collision instead.
- The script does not add explicit try/except around page counting or renaming; errors from corrupt PDFs or permission issues will propagate, so keep the logic simple unless adding handling is clearly beneficial.
- Be aware that the stem check is a substring test, so a file like `doc2024.pdf` with 4 pages may be skipped only if `"4"` appears in the stem; mention this limitation in comments if appropriate.

**Execution and usage:**
- Run from the directory containing the PDFs; it operates recursively from the current working directory.
- Make the script executable with the Termux Python shebang line at the top.
- Install at least one backend beforehand (`pip install pymupdf` preferred, or `pdfplumber` as fallback).
- Use the code style of the surrounding project: concise, typed, minimal comments, with PEP 8 naming and formatting.
---"""

from __future__ import annotations

import os
from collections.abc import Iterator
from multiprocessing import get_context
from pathlib import Path

try:
    import pymupdf  # type: ignore[import-untyped]

    _HAS_PYMUPDF = True
except ImportError:
    _HAS_PYMUPDF = False
    import pdfplumber


def walk_files(directory: str) -> Iterator[str]:
    for root, _dirs, files in os.walk(directory):
        for name in files:
            yield os.path.join(root, name)


def _page_count(path: Path) -> int:
    if _HAS_PYMUPDF:
        with pymupdf.open(path) as doc:
            return doc.page_count
    with pdfplumber.open(path) as pdf:
        return len(pdf.pages)


def process_file(path: str) -> None:
    p = Path(path)
    if p.exists() and not p.is_symlink():
        numpages = _page_count(p)
        new_name = p.stem + str(numpages) + ".pdf"
        print(new_name)
        np = Path(f"{p.parent}/{new_name}")
        if str(numpages) in p.stem:
            return
        if not np.exists():
            Path(p).rename(np)
            print(f"{p.name} --> {np.name}")
        else:
            print(f"{np.name} exists.")
    return


def main() -> None:
    files: list[Path] = []
    for pth in walk_files("."):
        path = Path(pth)
        if path.is_file() and path.suffix == ".pdf":
            files.append(path)
    with get_context("spawn").Pool(8) as pool:
        for _ in pool.imap_unordered(process_file, (str(f) for f in files)):
            pass


if __name__ == "__main__":
    raise SystemExit(main())
