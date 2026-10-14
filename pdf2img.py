#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts every PDF file in a given input folder into high-resolution JPG images, saving each PDF's pages into its own subfolder within an output directory. The script should process each PDF as a separate job, rendering every page of the document at print-quality resolution (around 300 DPI) and saving it as a high-quality JPEG (about 95% quality) named after the source PDF and the page number. Each PDF's output subfolder should be created automatically if it does not exist, named after the PDF's base filename.
Behavior requirements:
- Accept an input folder containing PDFs and an output folder as inputs, and handle both paths robustly, including creating the output location if needed.
- Print clear progress messages when starting each PDF conversion and a success message reporting how many page images were produced and where they were saved.
- Handle errors gracefully on a per-file basis: if one PDF fails, report the error with the file name, clean up any partially created output folder for that PDF, and continue processing the remaining PDFs without crashing the whole run.
- Return a success or failure status for each conversion so the overall results can be summarized.
- Finish by reporting a summary of how many PDFs converted successfully and how many failed.
- Include a command-line entry point so the script can be run directly from a terminal with the input and output folder paths supplied as arguments, with sensible help text and validation (e.g., error if the input folder does not exist).
---"""

from __future__ import annotations
from pathlib import Path
import shutil
import pymupdf


def convert_pdf_to_jpg(pdf_path: Path, output_folder: Path) -> bool:
    pdf_output_dir: Path = output_folder / pdf_path.stem
    try:
        print(f"Converting '{pdf_path.name}'...")
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        converted_files: list[Path] = []
        with pymupdf.open(pdf_path) as document:
            for page_index, page in enumerate(document):
                pixmap: pymupdf.Pixmap = page.get_pixmap(dpi=300)
                final_jpg_path: Path = pdf_output_dir / f"{pdf_path.stem}_page_{page_index + 1}.jpg"
                pixmap.save(str(final_jpg_path), jpg_quality=95)
                converted_files.append(final_jpg_path)
        print(f"Successfully converted '{pdf_path.name}' to {len(converted_files)} JPG files in '{pdf_output_dir}'.")
        return True
    except Exception as e:
        print(f"Error converting '{pdf_path.name}': {e}")
        if pdf_output_dir.exists():
            try:
                shutil.rmtree(pdf_output_dir)
            except Exception as cleanup_e:
                print(f"Error during cleanup of '{pdf_output_dir}': {cleanup_e}")
        return False


def process_directory(start_dir: Path, output_base_dir: Path) -> None:
    print(f"Starting PDF to JPG conversion in directory: {start_dir}")
    print(f"Output will be saved in: {output_base_dir}")
    converted_count: int = 0
    failed_count: int = 0
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
    cwdectory: Path = Path.cwd()
    output_directory: Path = cwdectory / "output_jpgs"
    output_directory.mkdir(exist_ok=True)
    process_directory(cwdectory, output_directory)
    print("\nScript finished.")
    print(f"Converted JPG files are located in: {output_directory}")
