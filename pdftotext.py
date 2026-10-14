#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that extracts plain text from PDF files supplied by the user on the command line. The tool should accept a path to a PDF, optionally support password-protected documents, let the user choose among multiple PDF parsing backends (with a sensible default), and produce the extracted text either to the console or to an output file. The extraction should process the document page by page, preserve page boundaries in the output so readers can tell where one page ends and the next begins, and optionally normalize whitespace (collapsing excess spaces and blank lines) while allowing that cleanup to be turned off. The text should be encoded using a configurable character encoding. The script should handle common failure cases gracefully, such as missing files, wrong or missing passwords, unsupported or unavailable backends, and corrupted PDFs, reporting clear error messages without crashing. Design the command-line interface so that all options have sensible defaults and a help message describing each one, and structure the code so the extraction logic can also be reused programmatically by other Python modules.
---"""

from __future__ import annotations
import argparse
from io import StringIO
from pathlib import Path
import re


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
            msg = f"Unsupported backend: {self.backend}"
            raise ValueError(msg)
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
