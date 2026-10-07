#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that merges multiple PDF files into a single output PDF using pypdf.
It should accept command-line arguments specifying individual PDF file paths and/or directories (from which it will collect all PDFs); if no arguments are given, it should default to all PDF files in the current working directory.
Files must be sorted by a numeric index extracted from filenames matching a trailing "_<number>.pdf" pattern, placing files without that pattern at the end.
The script should combine all pages from the sorted PDFs in order, write the result to "merged.pdf" in the current directory, print a message with the count of merged files and output path, and print a notice if no PDF files are found."""

from __future__ import annotations
import re
import sys
from pathlib import Path
from pypdf import PdfReader, PdfWriter


def extract_index(filename: str) -> tuple:
    match = re.search(r"_(\d+)\.pdf$", filename)
    if match:
        return (int(match.group(1)),)
    return (float("inf"),)


def merge_pdfs(input_paths=None, output_file: str = "merged.pdf") -> None:
    if input_paths is None or len(input_paths) == 0:
        pdf_files = sorted(Path.cwd().glob("*.pdf"), key=lambda p: extract_index(p.name))
    else:
        pdf_files = []
        for path in input_paths:
            p = Path(path)
            if p.is_file() and p.suffix.lower() == ".pdf":
                pdf_files.append(p)
            elif p.is_dir():
                pdf_files.extend(p.glob("*.pdf"))
        pdf_files = sorted(pdf_files, key=lambda p: extract_index(p.name))
    if not pdf_files:
        print("No PDF files found.")
        return
    writer = PdfWriter()
    for pdf_file in pdf_files:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            writer.add_page(page)
    output_path = Path.cwd() / output_file
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"Merged {len(pdf_files)} files into: {output_path}")


if __name__ == "__main__":
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    merge_pdfs(input_paths=args)
