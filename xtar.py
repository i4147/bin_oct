#!/data/data/com.termux/files/usr/bin/python
import gzip
import lzma
from multiprocessing import Pool
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile
import py7zr

MAX_WORKERS: int = 4
SUPPORTED_EXTENSIONS: set[str] = {
    ".tar.gz",
    ".tar.xz",
    ".tar.zst",
    ".tar.br",
    ".tgz",
    ".zip",
    ".whl",
    ".tar.lz4",
    ".tar.bz2",
    ".tar.7z",
}


def get_compression_type(path: Path) -> str | None:
    name: str = path.name.lower()
    if name.endswith((".tar.gz", ".tgz")):
        return "gz"
    elif name.endswith(".tar.xz"):
        return "xz"
    elif name.endswith(".tar.zst"):
        return "zst"
    elif name.endswith(".tar.br"):
        return "br"
    elif name.endswith(".tar.bz2"):
        return "bz2"
    elif name.endswith(".tar.lz4"):
        return "lz4"
    elif name.endswith(".tar.7z"):
        return "7z"
    elif name.endswith((".zip", ".whl")):
        return "zip"
    return None


def check_integrity(archive_path: Path) -> bool:
    compression: str | None = get_compression_type(archive_path)
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
            result: subprocess.CompletedProcess[str] = subprocess.run(
                ["zstd", "-t", str(archive_path)], capture_output=True, text=True
            )
            if result.returncode != 0:
                return False
        elif compression == "br":
            result = subprocess.run(["brotli", "-t", str(archive_path)], capture_output=True, text=True)
            if result.returncode != 0:
                return False
        elif compression == "bz2":
            import bz2

            with bz2.open(archive_path, "rb") as f:
                while f.read(1024 * 1024):
                    pass
        elif compression == "lz4":
            result = subprocess.run(["lz4", "-t", str(archive_path)], capture_output=True, text=True)
            if result.returncode != 0:
                return False
        elif compression == "7z":
            with py7zr.SevenZipFile(archive_path, mode="r") as z:
                z.test()
            return True
        elif compression == "zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                bad_file: str | None = zf.testzip()
                if bad_file is not None:
                    return False
            return True
        if compression in {"gz", "xz", "zst", "br", "bz2", "lz4"}:
            mode_map: dict[str, str] = {
                "gz": "r:gz",
                "xz": "r:xz",
                "zst": "r:",
                "br": "r:",
                "bz2": "r:bz2",
                "lz4": "r:",
            }
            with tarfile.open(archive_path, mode_map.get(compression, "r:*")) as tar:
                tar.getmembers()
        return True
    except (
        tarfile.TarError,
        lzma.LZMAError,
        gzip.BadGzipFile,
        zipfile.BadZipFile,
        OSError,
        subprocess.SubprocessError,
        py7zr.exceptions.Bad7zFile,
    ) as e:
        print(f"Integrity check failed for {archive_path.name}: {e}")
        return False


def extract_archive(archive_path: Path) -> bool:
    archive_path = Path(archive_path)
    print(f"Processing: {archive_path.name}")
    if not check_integrity(archive_path):
        print(f"Skipping {archive_path.name} (integrity check failed)")
        return False
    try:
        compression: str | None = get_compression_type(archive_path)
        if compression == "zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(path=archive_path.parent)
        elif compression == "7z":
            with py7zr.SevenZipFile(archive_path, mode="r") as z:
                z.extractall(path=archive_path.parent)
        else:
            mode_map: dict[str, str] = {
                "gz": "r:gz",
                "xz": "r:xz",
                "zst": "r:",
                "br": "r:",
                "bz2": "r:bz2",
                "lz4": "r:",
            }
            with tarfile.open(archive_path, mode_map.get(compression, "r:*")) as tar:
                tar.extractall(path=archive_path.parent, filter="data")
        archive_path.unlink()
        print(f"Successfully extracted and removed: {archive_path.name}")
        return True
    except (tarfile.TarError, OSError, EOFError, zipfile.BadZipFile, py7zr.exceptions.Bad7zFile) as e:
        print(f"Extraction failed for {archive_path.name}: {e}")
        return False


def find_archives(directory: str = ".") -> list[Path]:
    archives: list[Path] = []
    for pattern in SUPPORTED_EXTENSIONS:
        archives.extend(Path(directory).glob(f"*{pattern}"))
    return sorted(archives)


def main() -> None:
    archives: list[Path]
    if len(sys.argv) > 1:
        archives = [Path(arg) for arg in sys.argv[1:] if Path(arg).exists()]
    else:
        archives = find_archives()
    if not archives:
        print("No archive files found or specified.")
        print("Supported formats: .tar.gz, .tgz, .tar.xz, .tar.zst, .tar.br, .zip, .whl, .tar.lz4, .tar.bz2, .tar.7z")
        print("Usage: python extractor.py [archive1.tar.gz archive2.zip ...]")
        sys.exit(1)
    print(f"Found {len(archives)} archive(s) to process")
    print(f"Using {MAX_WORKERS} workers")
    print("-" * 40)
    with Pool(processes=MAX_WORKERS) as pool:
        results: list[bool] = pool.map(extract_archive, archives)
    successful: int = sum(1 for r in results if r)
    failed: int = sum(1 for r in results if not r)
    print("-" * 40)
    print(f"Summary: {successful} successful, {failed} failed/skipped")


if __name__ == "__main__":
    main()
