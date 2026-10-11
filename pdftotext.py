#!/data/data/com.termux/files/usr/bin/env python
"""The code is truncated at `elif self.b`, so I'll write the prompt based on what's visible and note the backend dispatch as it appears to continue.

Write a single, self-contained Python command-line script named as a PDF-to-text extractor with the following specifications.

**Purpose:** The script extracts text from a PDF file and writes it to an output file or standard output. It supports multiple interchangeable extraction backends and optional text normalization.

**Interface (argparse CLI):** Accept a required positional argument for the input PDF path. Provide optional arguments for: the backend choice (default `fitz`; supported values include `fitz`, `pypdf`, and `pdfplumber`, with one additional backend following in the dispatch chain), a password for encrypted PDFs (default empty string), an output encoding (default `utf-8`), an output file path (write to stdout if omitted), and a flag to disable space normalization. Use a shebang line pointing to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/env python`.

**Core design:** Define an `Extractor` class with constructor parameters `backend` (default `"fitz"`, stored lowercased), `password` (default `""`), `encoding` (default `"utf-8"`), and `normalize_spaces` (default `True`). Implement a method `extract_pages(pdf_path)` that converts the path to a `pathlib.Path` and returns a list of per-page text strings.

**Backend behavior:**
- `fitz` (PyMuPDF): import lazily inside the branch, open the document, call `authenticate` with the password only when one is provided, iterate pages calling `get_text()`, and close the document.
- `pypdf`: import `PdfReader` lazily, pass `password` to the constructor only when non-empty, and collect `extract_text()` per page, substituting an empty string when the result is `None`.
- `pdfplumber`: import lazily, build keyword arguments with `password` only when non-empty, open the file as a context manager, and collect `extract_text()` per page with the same `None`-to-empty fallback.
- Any other backend value must be handled by a final branch (the original code's dispatch continues past the visible portion; reproduce a sensible remaining backend such as a third library, and raise a clear error for unknown backends).

**Post-processing:** When `normalize_spaces` is enabled, collapse runs of whitespace within text (using regular expressions), and normalize line breaks so output is clean, while keeping page separation. Join pages into a single output string with clear page boundaries.

**Output:** Write the result using the configured encoding, to the output file if given, otherwise to standard output. Use `StringIO` where it helps build the output buffer.

**Dependencies:** Only the standard library is required at import time (`argparse`, `re`, `io`, `pathlib`). PyMuPDF (`fitz`), `pypdf`, and `pdfplumber` are imported lazily and are needed only for their respective backends. The script should not fail at import time if a backend library is missing; it should raise a clear error at extraction time identifying the missing package and suggesting how to install it.

**Error handling and edge cases:** Handle missing input files with a clear message, handle encrypted PDFs that lack or have the wrong password, handle pages that yield no text (treat as empty strings, not errors), and handle unknown backend names. Errors should be reported to the user with a non-zero exit status rather than an unhandled traceback where practical.

**Execution:** The script runs as `python <script> input.pdf [options]`, with an `if __name__ == "__main__":` entry point that parses arguments, constructs the `Extractor`, extracts pages, post-processes, and writes output.
---"""

import argparse
import re
from io import StringIO
from pathlib import Path


class Extractor(object):
    def __init__(
        self,
        backend="fitz",
        password="",
        encoding="utf-8",
        normalize_spaces=True,
    ):
        self.backend = backend.lower()
        self.password = password
        self.encoding = encoding
        self.normalize_spaces = normalize_spaces

    def extract_pages(self, pdf_path):
        pdf_path = Path(pdf_path)
        pages = []

        if self.backend == "fitz":
            import fitz

            doc = fitz.open(pdf_path)
            if self.password:
                doc.authenticate(self.password)
            for page in doc:
                pages.append(page.get_text())
            doc.close()

        elif self.backend == "pypdf":
            from pypdf import PdfReader

            reader = PdfReader(pdf_path, password=self.password) if self.password else PdfReader(pdf_path)
            for page in reader.pages:
                pages.append(page.extract_text() or "")

        elif self.backend == "pdfplumber":
            import pdfplumber

            kwargs = {"password": self.password} if self.password else {}
            with pdfplumber.open(pdf_path, **kwargs) as pdf:
                for page in pdf.pages:
                    pages.append(page.extract_text() or "")

        elif self.backend == "pdfminer":
            from pdfminer.converter import TextConverter
            from pdfminer.layout import LAParams
            from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
            from pdfminer.pdfpage import PDFPage

            rsrcmgr = PDFResourceManager(caching=True)
            laparams = LAParams(detect_vertical=True, char_margin=1.0, line_margin=0.3, word_margin=0.3)

            with open(pdf_path, "rb") as fp:
                for page in PDFPage.get_pages(fp, password=self.password, caching=True, check_extractable=True):
                    outfp = StringIO()
                    device = TextConverter(rsrcmgr, outfp, codec=self.encoding, laparams=laparams)
                    interpreter = PDFPageInterpreter(rsrcmgr, device)
                    interpreter.process_page(page)
                    pages.append(outfp.getvalue())
                    device.close()
                    outfp.close()
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

        if self.normalize_spaces:
            pages = [re.sub(r" +", " ", page) for page in pages]

        return pages

    def __call__(self, pdf_path):
        return "\n".join(self.extract_pages(pdf_path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdffiles", nargs="+")
    parser.add_argument("-p", "--perpage", action="store_true")
    parser.add_argument(
        "-b",
        "--backend",
        default="fitz",
        choices=["fitz", "pypdf", "pdfplumber", "pdfminer"],
    )
    parser.add_argument("--password", default="")
    args = parser.parse_args()

    extractor = Extractor(
        backend=args.backend,
        password=args.password,
    )

    for fname in args.pdffiles:
        pdf_path = Path(fname)
        if not pdf_path.exists():
            continue

        pages = extractor.extract_pages(pdf_path)

        if args.perpage:
            out_dir = pdf_path.parent / pdf_path.stem
            out_dir.mkdir(parents=True, exist_ok=True)
            for idx, page_text in enumerate(pages, start=1):
                out_file = out_dir / f"page_{idx}.txt"
                out_file.write_text(page_text, encoding="utf-8")
        else:
            print("\n".join(pages))


if __name__ == "__main__":
    main()
