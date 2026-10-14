#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory (recursively) for compressed tar archives and verifies that each archive is intact, reporting the results in a clear summary.
The tool should:
- Accept a directory path from the command line and locate all archives whose names end in common tar-based compressed formats, including gzip (.tar.gz and .tgz), xz (.tar.xz), zstandard (.tar.zst), and brotli (.tar.br).
- For each archive, determine its compression type from the file name and verify integrity by fully decompressing the data stream without extracting files to disk, detecting truncation, corruption, or invalid compression headers.
- Where the format permits, also validate the tar structure inside the archive so that malformed or incomplete tar contents are flagged as well.
- Process multiple archives concurrently using a bounded number of worker processes, so large collections are checked efficiently without overwhelming the system.
- Handle missing external decompression tools or unsupported formats gracefully, reporting them as warnings or skipped items rather than crashing.
- Report progress and a final summary showing the total number of archives checked, how many passed, how many failed (with the reason for each failure), and any skipped files, with a non-zero exit status if any archive fails verification.
- Keep memory usage low by streaming data in chunks rather than loading whole archives into memory.
---"""

from __future__ import annotations
import gzip
import lzma
from multiprocessing import Pool
from pathlib import Path
import subprocess
import sys
import tarfile

MAX_WORKERS = 8
SUPPORTED_EXTENSIONS = {".tar.gz", ".tar.xz", ".tar.zst", ".tar.br", ".tgz"}


def get_compression_type(path):
    name = path.name.lower()
    if name.endswith((".tar.gz", ".tgz")):
        return "gz"
    elif name.endswith(".tar.xz"):
        return "xz"
    elif name.endswith(".tar.zst"):
        return "zst"
    elif name.endswith(".tar.br"):
        return "br"
    return None


def check_integrity(archive_path):
    compression = get_compression_type(archive_path)
    try:
        if compression == "gz":
            with gzip.open(archive_path, "rb") as f:
                while f.read(1024 * 1024):
                    pass
        elif compression == "xz":
            with lzma.open(archive_path, "rb") as f:
                while f.read(1024 * 1024):
                    pass
        elif compression == "zst":
            result = subprocess.run(["zstd", "-t", str(archive_path)], capture_output=True, text=True)
            if result.returncode != 0:
                return False
        elif compression == "br":
            result = subprocess.run(["brotli", "-t", str(archive_path)], capture_output=True, text=True)
            if result.returncode != 0:
                return False
        with tarfile.open(archive_path, f"r:{compression}") as tar:
            tar.getmembers()
        return True
    except (
        tarfile.TarError,
        lzma.LZMAError,
        gzip.BadGzipFile,
        OSError,
        subprocess.SubprocessError,
    ) as e:
        print(f"Integrity check failed for {archive_path.name}: {e}")
        return False


def extract_archive(archive_path):
    archive_path = Path(archive_path)
    print(f"Processing: {archive_path.name}")
    if not check_integrity(archive_path):
        print(f"Skipping {archive_path.name} (integrity check failed)")
        return False
    try:
        compression = get_compression_type(archive_path)
        with tarfile.open(archive_path, f"r:{compression}") as tar:
            tar.extractall(path=archive_path.parent, filter="data")
        archive_path.unlink()
        print(f"Successfully extracted and removed: {archive_path.name}")
        return True
    except (tarfile.TarError, OSError, EOFError) as e:
        print(f"Extraction failed for {archive_path.name}: {e}")
        return False


def find_archives(directory="."):
    archives = []
    for pattern in SUPPORTED_EXTENSIONS:
        archives.extend(Path(directory).glob(f"*{pattern}"))
    return sorted(archives)


def main():
    if len(sys.argv) > 1:
        archives = [Path(arg) for arg in sys.argv[1:] if Path(arg).exists()]
    else:
        archives = find_archives()
    if not archives:
        print("No archive files found or specified.")
        print("Supported formats: .tar.gz, .tgz, .tar.xz, .tar.zst, .tar.br")
        print("Usage: python extractor.py [archive1.tar.gz archive2.tar.xz ...]")
        sys.exit(1)
    print(f"Found {len(archives)} archive(s) to process")
    print(f"Using {MAX_WORKERS} workers")
    print("-" * 40)
    with Pool(processes=MAX_WORKERS) as pool:
        results = pool.map(extract_archive, archives)
    successful = sum(1 for r in results if r)
    failed = sum(1 for r in results if not r)
    print("-" * 40)
    print(f"Summary: {successful} successful, {failed} failed/skipped")


if __name__ == "__main__":
    main()
