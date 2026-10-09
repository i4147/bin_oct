#!/data/data/com.termux/files/usr/bin/env python
"""Write a prompt for an AI coding agent that will generate a Python command-line script with the following specifications:

**Purpose:** Build a PDF text extraction tool designed to run in a Termux) environment, capable of extracting text from PDF files using multiple interchangeable backend libraries.

**Environment:** The script must use the Termux Python shebang (`#!/data/data/com.termux/files/usr/bin/python3.12`) and be a standalone executable CLI tool.

**Core design:**
- Implement an `Extractor` class that encapsulates all extraction logic, config-extraction library to use ( atitz` (PyMuPDF), `pypdf`, `pdfplumber`, and `pdfminer`, selectable via a string, case-insensitive)
  - `password`: optional password for encrypted PDFs
  - `encoding`: output text encoding (default `utf-8`)
  - `normalize_spaces`: boolean flag to control whitespace normalization of extracted text

- The class should have a method `extract_pages(pdf_path)` that:
  - Accepts a path to a PDF file (convert to a `Path` object internally)
  - Dynamically imports the required backend library only when that backend is selected (lazy imports, so users don't need all libraries installed, only the one they use)
  - Opens the PDF with the chosen backend, applying the password if provided and supported by that backend's API
  - Iterates through all pages of the PDF, extracting text per page
  - Handles each backend's specific API differences correctly:
    - `fitz` (PyMuPDF): open document, authenticate with password if given, call `get_text()` on each page, then close the document
    - `pypdf`: use `PdfReader` with passwordided, call `extract_textallback to empty string if `None`)
    - `pdfplumber`: open with `pdfplumber.open`, passing password as kwarg only if provided, call `extract_text()` on each page (fallback to empty string if `None`)
    - `pdfminer`: use the low-level `pdfminer` API (`PDFResourceManager`, `PDFPageInterpreter`, `TextConverter`, `LAParams`, and an in-memory `StringIO` buffer) to extract text page by page
  - Returns a list of strings, one per page, containing the raw/extracted text

**Additional requirements:**
- Use `argparse` to build a command-line interface around this functionality (accepting at least the PDF file path, backend choice, password, encoding, and an option to control space normalization; also support specifying anracted text)
- Use the `re` module tosing multiple spaces/newlines when `normalize_spacesinclude a `mainarded by `if __name__ == "__main__":`)
- Write cleanured Python code with appropriate error and backends that aren't installed.

Generate the complete Python script implementing this behavior.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/7iF6vfHXZD4qmEgG8kPRMx"""

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
