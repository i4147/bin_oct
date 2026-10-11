#!/data/data/com.termux/files/usr/bin/python
"""Write a self-contained Python command-line script that OCRs a PDF file and prints the extracted text to standard output. Requirements:

**Purpose:** Extract text from every page of a PDF using OCR (optical character recognition), processing pages in parallel across multiple worker processes, and print the combined result.

**Interface:**
- Run as a script with a single positional command-line argument: the path to a PDF file.
- Output the full extracted text to stdout, with page texts joined by newline characters, in page order.
- The script's shebang should point to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/python`.

**Dependencies:**
- Use the `pymupdf` library (PyMuPDF) for opening PDFs, loading pages, and performing OCR via its page text-page OCR method, using English language, 300 DPI, full-page mode, and flags set to 0.
- Use Python's standard `multiprocessing` module for a process pool, `pathlib.Path` for file paths, and `typing.Optional` for type hints.
- Use type annotations throughout (e.g., `Optional[pymupdf.Document]`, `list[str]`, `pymupdf.Page`, `pymupdf.TextPage`).

**Key logic:**
1. Define a module-level variable holding a PDF document handle, initially `None`.
2. Define a worker initializer function that takes a PDF path string and opens the document into that module-level variable. Each worker process opens its own document handle, since handles cannot be shared across processes.
3. Define a per-page worker function that takes a zero-based page number, asserts the document handle is initialized, loads the page, obtains an OCR text page (English, 300 DPI, full=True, flags=0), and returns the text extracted from that page using the text-page option.
4. Define a main function `extract_text(pdf_path: Path, workers: int = 4) -> str` that:
   - Opens the PDF briefly (in a context manager) to read its page count.
   - Creates a multiprocessing pool with `workers` processes, using the initializer with the PDF path as a string argument.
   - Maps the per-page function over `range(page_count)` using `pool.map` so results preserve page order.
   - Returns the page texts joined with `"\\n"`.
5. In the `__main__` guard: import `sys`, convert `sys.argv[1]` to a `Path`, call `extract_text` with `workers=4`, and print the result.

**Error handling and edge cases:**
- The script has no explicit try/except; errors such as a missing argument (IndexError), a nonexistent or unreadable file, or a non-PDF file propagate as exceptions.
- The worker function uses an `assert` to guarantee the document is initialized; preserve this.
- A PDF with zero pages should yield an empty string (the pool maps over an empty range, and the join returns `""`).
- Use the context manager for the pool and for the initial document open so resources are released.
- Pass the path to workers as a string, not a `Path` object.

**Usage:**
- Invocation: `python <script> <path-to-pdf>`
- Example: the script prints OCR text for all pages to the terminal; redirect stdout to save it to a file.
- Performance note: OCR at 300 DPI is CPU-intensive; the worker count is fixed at 4 in the main block.
---"""

import multiprocessing as mp
from pathlib import Path
from typing import Optional

import pymupdf

_DOC: Optional[pymupdf.Document] = None


def _init_worker(pdf_path: str) -> None:
    global _DOC
    _DOC = pymupdf.open(pdf_path)


def _ocr_page(page_num: int) -> str:
    assert _DOC is not None
    page: pymupdf.Page = _DOC.load_page(page_num)
    textpage: pymupdf.TextPage = page.get_textpage_ocr(flags=0, language="eng", dpi=300, full=True)
    return page.get_text("text", textpage=textpage)


def extract_text(pdf_path: Path, workers: int = 4) -> str:
    with pymupdf.open(str(pdf_path)) as doc:
        page_count: int = doc.page_count
    with mp.Pool(
        processes=workers,
        initializer=_init_worker,
        initargs=(str(pdf_path),),
    ) as pool:
        pages: list[str] = pool.map(_ocr_page, range(page_count))
    return "\n".join(pages)


if __name__ == "__main__":
    import sys

    pdf_file = Path(sys.argv[1])
    print(extract_text(pdf_file, workers=4))
