#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that processes a PDF file by splitting it into individual single-page PDF files and extracting the text content of each page into separate text files. The script should accept a path to an input PDF and an output directory as inputs, creating the output directory if it does not exist. For each page of the source document, it should produce one standalone PDF file containing only that page, and one plain-text file containing the extracted text of that page. Output filenames should be derived from the original document's base name, followed by a zero-padded page number whose width adapts to the total page count, so files sort correctly in order. The script should process pages efficiently, may use parallel execution for independent per-page work, and must properly close all document resources. It should handle common errors gracefully, such as missing input files, unreadable or encrypted PDFs, and unwritable output locations, by reporting clear messages to the user rather than crashing silently. Provide a command-line interface that accepts the input PDF path and optional output directory, and print a concise summary upon completion indicating how many pages were processed and where the results were saved.
---"""

from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import pymupdf


def split_pdf_by_page(pdf_path: Path, output_dir: Path) -> None:
    with pymupdf.open(pdf_path) as document:
        stem: str = pdf_path.stem
        total_pages: int = document.page_count
        padding: int = len(str(total_pages))
        for page_index in range(total_pages):
            new_doc: pymupdf.Document = pymupdf.open()
            new_doc.insert_pdf(document, from_page=page_index, to_page=page_index)
            padded_num: str = str(page_index + 1).zfill(padding)
            output_path: Path = output_dir / f"{stem}_{padded_num}.pdf"
            new_doc.save(str(output_path))
            new_doc.close()


def extract_text_by_page(pdf_path: Path, output_dir: Path) -> None:
    with pymupdf.open(pdf_path) as document:
        stem: str = pdf_path.stem
        total_pages: int = document.page_count
        padding: int = len(str(total_pages))
        for page_index in range(total_pages):
            page: pymupdf.Page = document.load_page(page_index)
            text: str = page.get_text()
            padded_num: str = str(page_index + 1).zfill(padding)
            output_path: Path = output_dir / f"{stem}_{padded_num}.txt"
            output_path.write_text(text, encoding="utf-8")


def process_pdfs(
    input_paths: list[str] | None = None,
    output_dir: Path | None = None,
    text_mode: bool = False,
) -> None:
    if output_dir is None:
        output_dir = Path.cwd() / "output"
    output_dir.mkdir(exist_ok=True)
    pdf_files: list[Path] = []
    if input_paths is None or len(input_paths) == 0:
        pdf_files = list(Path.cwd().rglob("*.pdf"))
    else:
        for path in input_paths:
            p: Path = Path(path)
            if p.is_file() and p.suffix.lower() == ".pdf":
                pdf_files.append(p)
            elif p.is_dir():
                pdf_files.extend(p.rglob("*.pdf"))
    if not pdf_files:
        print("No PDF files found.")
        return
    worker = extract_text_by_page if text_mode else split_pdf_by_page
    with ThreadPoolExecutor() as executor:
        for pdf_file in pdf_files:
            executor.submit(worker, pdf_file, output_dir)
    print(f"Processing complete. Output files in: {output_dir}")


if __name__ == "__main__":
    raw_args: list[str] = sys.argv[1:]
    text_mode: bool = False
    if "-t" in raw_args:
        text_mode = True
        raw_args.remove("-t")
    input_paths: list[str] | None = raw_args or None
    process_pdfs(input_paths=input_paths, text_mode=text_mode)
