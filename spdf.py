#!/data/data/com.termux/files/usr/bin/python3.12
"""Create a command-line Python script (intended to run on Termux/Android under `/data/data/com.termux/files/usr/bin/python3.12`, but should work generally on Linux systems with Ghostscript installed) that batch-compresses PDF files using Ghostscript.

**Purpose:**
Compress one or more PDF files in parallel to reduce their file size, using Ghostscript's `/ebook` quality preset while also downsampling and compressing fonts/images for additional savings.

**Main inputs:**
- Accepts one or more PDF file paths as command-line arguments (via `argparse`).
- Optionally support other reasonable CLI flags, such as number of parallel worker processes.

**Main outputs:**
- For each valid input PDF, the script compresses it with Ghostscript into a temporary output file first (using `tempfile.mkstemp`), using settings such as:
  - `-sDEVICE=pdfwrite`
  - `-dCompatibilityLevel=1.4`
  - `-dPDFSETTINGS=/ebook`
  - `-dNOPAUSE -dQUIET -dBATCH`
  - `-dDetectDuplicateImages=true`
  - `-dCompressFonts=true`
  - `-dDownsampleColownsampleGrayImages=true -dGrayImageResolution=150`
  - `-dDownsampleMonoImages=true -dMonoImageResolution=150` Compares the original file size against the compressed file size.
- Only replaces the original file with the compressed version if the compressed version is actually smaller; otherwise keeps the original and discards the temporary file.
- Logs progress, warnings, and errors using `loguru` (e.g., skipping non-PDF/missing files, Ghostscript failures, size comparison results).
- Returns per-file results (e.g., a tuple of path, original size, compressed size) so a summary can be reported aftermultiprocessing.urrently for speed.
- Validates that exists and has a `.pdf` extension (case-insensitive); skips and logs a warning otherwise instead of raising an error.
- Invokes Ghostscript (`gs`) via `subprocess.run`, capturing stdout/stderr, and handles non-zero return codes gracefully by logging the Ghostscript error output and returning `None` for that file (not crashing the whole batch).
- Uses `tempfile` for safe intermediate output and ensures temporary files are cleaned up (e.g., via `contextlib` or explicit cleanup) even on failure, using `shutil` to move/replace files when compression succeeds.
- Designed to be safe to run on many files at once without one failure stopping the rest of the batch.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/gGCK3bMxJ5YRCXbdGRy39L"""

from __future__ import annotations
import argparse
import contextlib
import shutil
import subprocess
import tempfile
from multiprocessing import Pool
from pathlib import Path
from typing import List, Optional, Tuple
from loguru import logger


def compress_pdf(input_path: Path) -> Optional[tuple[Path, int, int]]:
    input_path = input_path.resolve()
    if not input_path.exists() or input_path.suffix.lower() != ".pdf":
        logger.warning(f"Skipping non-PDF or missing file: {input_path}")
        return None
    _temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        gs_command = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/ebook",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dDetectDuplicateImages=true",
            "-dCompressFonts=true",
            "-dDownsampleColorImages=true",
            "-dColorImageResolution=150",
            "-dDownsampleGrayImages=true",
            "-dGrayImageResolution=150",
            "-dDownsampleMonoImages=true",
            "-dMonoImageResolution=150",
            f"-sOutputFile={temp_path}",
            str(input_path),
        ]
        result = subprocess.run(gs_command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            logger.error(f"Ghostscript failed for {input_path.name}: {result.stderr}")
            return None
        original_size = input_path.stat().st_size
        compressed_size = Path(temp_path).stat().st_size
        if compressed_size >= original_size:
            logger.info(
                f"Skipped {input_path.name}: compressed size ({compressed_size:,} bytes) >= original ({original_size:,} bytes)"
            )
            return None
        shutil.move(temp_path, input_path)
        reduction_pct = ((original_size - compressed_size) / original_size) * 100
        space_saved = original_size - compressed_size
        logger.success(
            f"{input_path.name}: {original_size:,} → {compressed_size:,} bytes "
            f"| Saved: {space_saved:,} bytes ({reduction_pct:.1f}%)"
        )
        return (input_path, original_size, compressed_size)
    except Exception as e:
        logger.error(f"Error processing {input_path.name}: {e}")
        return None
    finally:
        with contextlib.suppress(BaseException):
            Path(temp_path).unlink(missing_ok=True)


def collect_pdf_files(paths: list[Path]) -> list[Path]:
    pdf_files: list[Path] = []
    for path in paths:
        path = path.resolve()
        if path.is_file() and path.suffix.lower() == ".pdf":
            pdf_files.append(path)
        elif path.is_dir():
            pdf_files.extend(path.rglob("*.pdf"))
    return pdf_files


def format_bytes(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="*", help="PDF files or directories to process")
    args = parser.parse_args()
    if args.inputs:
        input_paths = [Path(p) for p in args.inputs]
    else:
        input_paths = [Path.cwd()]
    pdf_files = collect_pdf_files(input_paths)
    if not pdf_files:
        logger.warning("No PDF files found to process")
        return
    logger.info(f"Found {len(pdf_files)} PDF file(s) to process")
    total_before = sum(f.stat().st_size for f in pdf_files)
    with Pool(processes=4) as pool:
        results = list(pool.imap_unordered(compress_pdf, pdf_files))
    total_after = sum(f.stat().st_size for f in pdf_files)
    freed_space = total_before - total_after
    logger.info("=" * 70)
    logger.info("COMPRESSION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Files processed: {len(pdf_files)}")
    logger.info(f"Directory size before: {format_bytes(total_before)}")
    logger.info(f"Directory size after: {format_bytes(total_after)}")
    if freed_space > 0:
        reduction_pct = (freed_space / total_before) * 100
        logger.success(f"Space freed: {format_bytes(freed_space)} ({reduction_pct:.2f}%)")
    else:
        logger.warning("No space freed - all files were already optimally compressed")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
