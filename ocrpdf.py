#!/data/data/com.termux/files/usr/bin/python
from pathlib import Path
from typing import Optional
import multiprocessing as mp
import pymupdf

_DOC: Optional[pymupdf.Document] = None


def _init_worker(pdf_path: str) -> None:
    global _DOC
    _DOC = pymupdf.open(pdf_path)


def _ocr_page(page_num: int) -> str:
    assert _DOC is not None
    page: pymupdf.Page = _DOC.load_page(page_num)
    textpage: pymupdf.TextPage = page.get_textpage_ocr(
        flags=0, language="eng", dpi=300, full=True
    )
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
