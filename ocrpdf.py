#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that extracts the full text content from a PDF file using optical character recognition, so it worksages as well as native text. The script should accept the path to a PDF file as a command-line argument and print the combined text of all pages to standard output, with pages kept in their original order and separated by line breaks.
Because OCR on high-resolution page renders is slow, the script should process pages in parallel across a configurable number of worker processes (default four), with each worker opening its own handle to the document so that the work is truly distributed. The OCR should be English-language, run at a print-quality resolution of about 300 DPI, and cover the full page area. The script should read the document's page count up front, then distribute the pages across the workers and collect results in order, ensuring the final output is deterministic and complete. Make sure resources are released cleanly once processing finishes, and ensure the script is safe to run as a standalone program on platforms that spawn new processes.
---"""

from __future__ import annotations
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
