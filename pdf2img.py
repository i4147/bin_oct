#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that instructs an AI coding agent to write a Python script with the following specification:

Write a single-file Python script (Termux-compatible, with a `/data/data/com.termux/files/usr/bin/env python` shebang) that converts PDF files into JPEG images, one folder per PDF, using the `pdf2image` library. The script should begin with `from __future__ import annotations` and import `shutil`, `pathlib.Path`, and `convert_from_path` from `pdf2image`. Define a module-level constant `POPPLER_PATH` set to `None` so users can point it at a Poppler binary directory if needed.

Implement a function `convert_pdf_to_jpg(pdf_path: Path, output_folder: Path) -> bool` with these behaviors:

- Print a progress line naming the PDF file (name only, not full path) before converting.
- Create a subfolder inside `output_folder` named after the PDF's stem (filename without extension), creating parent directories as needed and tolerating an existing folder.
- Call `convert_from_path` with 300 DPI, JPEG format, 4 threads, the per-PDF subfolder as the output folder, and `POPPLER_PATH` as the Poppler path.
- Note that `convert_from_path` writes files named with a `jpeg` extension using the pattern `<stem>_page_<n>.jpeg` (1-based page numbers). For each returned page, locate that expected file in the subfolder; if it exists, rename it to a `.jpg` extension with the same stem and page number using `shutil.move`, and record it. If it does not exist, print a warning naming the expected path and continue.
- After processing, print a success message stating how many JPG files were produced and the output directory.
- Return `True` on success. Wrap the whole operation in a broad `try/except Exception`; on error, print an error message identifying the PDF file name and the exception, and return `False`.

The script should also include a `main` entry point (guarded by `if __name__ == "__main__":`) that performs the batch workflow: it should accept or determine a source directory containing PDFs and an output directory, iterate over all `.pdf` files, call `convert_pdf_to_jpg` for each, and report a summary of successes and failures. Use `pathlib` for all path handling. Handle the case where no PDFs are found by printing a clear message rather than failing silently. Use `print` for all user-facing output (no logging framework required).

Usage and environment notes: the script targets Termux on Android, so `pdf2image` requires the Poppler utilities (`pdftoppm`) to be installed in the environment; if `POPPLER_PATH` is `None`, Poppler must be on the system PATH. Keep the code dependency-light, standard-library-plus-`pdf2image` only, and avoid any non-essential features. Use type hints throughout and match the terse, readable style of a small utility script.
---"""

from __future__ import annotations

import shutil
from pathlib import Path

from pdf2image import convert_from_path

POPPLER_PATH = None


def convert_pdf_to_jpg(pdf_path: Path, output_folder: Path) -> bool:
    try:
        print(f"Converting '{pdf_path.name}'...")
        pdf_output_dir = output_folder / pdf_path.stem
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        images = convert_from_path(
            pdf_path=pdf_path,
            dpi=300,
            output_folder=pdf_output_dir,
            fmt="jpeg",
            thread_count=4,
            poppler_path=POPPLER_PATH,
        )
        converted_files = []
        for i, _image_path in enumerate(images):
            expected_jpg_name = f"{pdf_path.stem}_page_{i + 1}.jpeg"
            source_jpg_path = pdf_output_dir / expected_jpg_name
            if source_jpg_path.exists():
                final_jpg_path = pdf_output_dir / f"{pdf_path.stem}_page_{i + 1}.jpg"
                shutil.move(source_jpg_path, final_jpg_path)
                converted_files.append(final_jpg_path)
            else:
                print(f"Warning: Expected file {source_jpg_path} not found after conversion.")
        print(f"Successfully converted '{pdf_path.name}' to {len(converted_files)} JPG files in '{pdf_output_dir}'.")
        return True
    except Exception as e:
        print(f"Error converting '{pdf_path.name}': {e}")
        if "pdf_output_dir" in locals() and pdf_output_dir.exists():
            try:
                shutil.rmtree(pdf_output_dir)
            except Exception as cleanup_e:
                print(f"Error during cleanup of '{pdf_output_dir}': {cleanup_e}")
        return False


def process_directory(start_dir: Path, output_base_dir: Path) -> None:
    print(f"Starting PDF to JPG conversion in directory: {start_dir}")
    print(f"Output will be saved in: {output_base_dir}")
    converted_count = 0
    failed_count = 0
    for item in start_dir.rglob("*"):
        if item.is_file() and item.suffix.lower() == ".pdf":
            if output_base_dir in item.parents:
                print(f"Skipping PDF '{item.name}' as it's within the output directory.")
                continue
            if convert_pdf_to_jpg(item, output_base_dir):
                try:
                    item.unlink()
                    print(f"Removed original PDF: '{item.name}'")
                    converted_count += 1
                except OSError as e:
                    print(f"Error removing original PDF '{item.name}': {e}")
                    failed_count += 1
            else:
                failed_count += 1
    print("\n--- Conversion Summary ---")
    print(f"Successfully converted and removed: {converted_count} PDF files.")
    print(f"Failed to convert: {failed_count} PDF files.")
    print("------------------------")


if __name__ == "__main__":
    cwdectory = Path.cwd()
    output_directory = cwdectory / "output_jpgs"
    output_directory.mkdir(exist_ok=True)
    process_directory(cwdectory, output_directory)
    print("\nScript finished.")
    print(f"Converted JPG files are located in: {output_directory}")
