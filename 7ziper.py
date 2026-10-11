#!/data/data/com.termux/files/usr/bin/env python
"""The code provided is truncated at the end (it stops mid-line in `_log_error`), so the prompt below describes the full intended behavior as far as it can be inferred from what is visible, and flags the truncated portion.

Write a Python 3 script that acts as a Termux-friendly archive packer and compression benchmarker built on the py7zr library. It should be runnable as an executable with the shebang `#!/data/data/com.termux/files/usr/bin/env python`, and use `from __future__ import annotations` for type hints.

**Dependencies and imports:**
- Standard library only, plus `py7zr` (required) and `loguru` (optional). Use `argparse`, `logging`, `mmap`, `multiprocessing`, `shutil`, `sys`, `tarfile`, `tempfile`, `concurrent.futures.ProcessPoolExecutor`, `pathlib.Path`, and `typing` (`Any`, `Dict`, `List`, `Optional`, `Tuple`).
- Attempt to import `loguru`'s logger as `_log`; if the import fails, set `_log` to `None` and fall back to the standard `logging` module.

**Module constants:**
- `_BASIC_SKIP_SUFFIXES`: set of file suffixes to skip in basic mode, namely `.7z`, `.xz`, `.br`, `.zst`, `.gz`, `.zip`, `.whl`, `.log`.
- `_NAMED_SKIP_SUFFIXES`: set of suffixes to skip in named mode, namely `.tar`, `.7z`, `.br`, `.gz`, `.xz`, `.zip`, `.whl`.
- `_FULL_SKIP_SUFFIXES`: tuple of suffixes to skip in full mode, namely `.7z`, `.xz`, `.gz`, `.bz2`, `.br`, `.zst`, `.zip`, `.rar`.
- `_NAMED_METHODS`: tuple `("LZMA2", "LZMA", "PPMd")` of compression methods to try in named mode.
- `_FULL_SETTINGS`: a dict of py7zr write options: an LZMA2 filter at preset 9, dictionary size 268435456 bytes (256 MiB), solid archive enabled, header compression enabled, and block size 4194304 bytes (4 MiB).

**Logging helpers:**
- Implement `_log_info`, `_log_warning`, and `_log_error`. Each takes a message template and optional positional args. When `_log` is available, format the message with `str.format(*args)` if args are given and call the loguru method; otherwise pass the template and args directly to the corresponding `logging` function.

**Expected behavior (inferred from the module design):**
- Provide a command-line interface via `argparse` that accepts an input path (file or directory) and an output location, and selects a mode (basic, named, or full) that determines which compression methods and skip-suffix rules apply.
- In full mode, use `_FULL_SETTINGS` when writing 7z archives via py7zr.
- In named mode, iterate over `_NAMED_METHODS`, trying each method when creating archives.
- Skip files matching the mode's suffix set, logging skipped items.
- Use `tempfile` for intermediate staging and `shutil` for file operations; use `tarfile` for tar-based packaging where relevant.
- Use `mmap` for efficient reading of large files where appropriate.
- Use `ProcessPoolExecutor` (with `multiprocessing`) to compress multiple files or variants in parallel, returning results as `(name, result)`-style tuples typed with `Tuple`, `Dict`, and `List`.
- Report sizes and compression ratios per variant and a summary, and handle errors per item without aborting the whole run, logging failures through the helpers.
- Guard the entry point with `if __name__ == "__main__":` and exit with `sys.exit` using a nonzero status on fatal errors.

**Edge cases to handle:** missing or unreadable inputs, empty directories, skipped suffixes, temp-directory cleanup even on failure, and the optional absence of `loguru`.

**Note:** The source was truncated at the `_log_error` helper, so the remainder of the script (the main logic and CLI) must be designed to fit these constants and helpers consistently.
---"""

from __future__ import annotations

import argparse
import logging
import mmap
import multiprocessing
import shutil
import sys
import tarfile
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import py7zr

try:
    from loguru import logger as _log
except ImportError:
    _log = None
_BASIC_SKIP_SUFFIXES = {".7z", ".xz", ".br", ".zst", ".gz", ".zip", ".whl", ".log"}
_NAMED_SKIP_SUFFIXES = {".tar", ".7z", ".br", ".gz", ".xz", ".zip", ".whl"}
_FULL_SKIP_SUFFIXES = (".7z", ".xz", ".gz", ".bz2", ".br", ".zst", ".zip", ".rar")
_NAMED_METHODS = ("LZMA2", "LZMA", "PPMd")
_FULL_SETTINGS: dict[str, Any] = {
    "filters": [{"id": py7zr.FILTER_LZMA2, "preset": 9}],
    "dictionary_size": 268435456,
    "solid": True,
    "header_compression": True,
    "block_size": 4194304,
}


def _log_info(msg: str, *args: Any) -> None:
    if _log is not None:
        _log.info(msg.format(*args) if args else msg)
    else:
        logging.info(msg, *args)


def _log_warning(msg: str, *args: Any) -> None:
    if _log is not None:
        _log.warning(msg.format(*args) if args else msg)
    else:
        logging.warning(msg, *args)


def _log_error(msg: str, *args: Any) -> None:
    if _log is not None:
        _log.error(msg.format(*args) if args else msg)
    else:
        logging.error(msg, *args)


def _human_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024.0:
            return f"{num:.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} PB"


def _sevenzip_write(
    dst: Path,
    preset: int = 9,
    filters: Optional[list] = None,
    **kwargs: Any,
) -> py7zr.SevenZipFile:
    if filters is None:
        filters = [{"id": py7zr.FILTER_LZMA2, "preset": preset}]
    return py7zr.SevenZipFile(dst, mode="w", filters=filters, **kwargs)


def _basic_setup_logging(log_file: Path) -> None:
    fmt = logging.Formatter("%(asctime)s [%(levelname)s]%(processName)s%(message)s")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.addHandler(fh)
    root.addHandler(sh)


def _basic_iter_dirs(base: Path):
    for p in base.iterdir():
        if p.is_dir() and not p.is_symlink():
            yield p


def _basic_iter_files(base: Path):
    for p in base.iterdir():
        if p.is_file() and not p.is_symlink() and p.suffix not in _BASIC_SKIP_SUFFIXES:
            yield p


def _basic_compress_dir(payload: tuple[str, int]) -> tuple[str, bool, str]:
    path_str, preset = payload
    path = Path(path_str)
    tar_path = path.with_suffix(".tar")
    archive_path = path.with_suffix(".tar.7z")
    try:
        if tar_path.exists():
            tar_path.unlink()
        with tarfile.open(tar_path, mode="w") as tar:
            tar.add(path, arcname=path.name)
        if archive_path.exists():
            archive_path.unlink()
        with _sevenzip_write(archive_path, preset=preset) as archive:
            archive.write(tar_path, arcname=tar_path.name)
        shutil.rmtree(path)
        tar_path.unlink(missing_ok=True)
        return (str(path), True, f"Compressed directory -> {archive_path.name}")
    except Exception as exc:
        logging.exception("Error compressing directory %s", path)
        try:
            if tar_path.exists():
                tar_path.unlink()
        except Exception:
            logging.exception("Failed to cleanup tar %s", tar_path)
        return (str(path), False, f"{type(exc).__name__}: {exc}")


def _basic_compress_file(payload: tuple[str, int]) -> tuple[str, bool, str]:
    path_str, preset = payload
    path = Path(path_str)
    archive_path = path.with_suffix(path.suffix + ".7z") if path.suffix else path.with_name(path.name + ".7z")
    try:
        if archive_path.exists():
            archive_path.unlink()
        with _sevenzip_write(archive_path, preset=preset) as archive:
            archive.write(path, arcname=path.name)
        path.unlink()
        return (str(path), True, f"Compressed file -> {archive_path.name}")
    except Exception as exc:
        logging.exception("Error compressing file %s", path)
        try:
            if archive_path.exists():
                archive_path.unlink()
        except Exception:
            logging.exception("Failed to cleanup archive %s", archive_path)
        return (str(path), False, f"{type(exc).__name__}: {exc}")


def run_basic(args: argparse.Namespace) -> int:
    base = Path.cwd()
    log_file = base / args.log_file
    _basic_setup_logging(log_file)
    logging.info("Starting compression in %s", base)
    preset = args.preset
    dirs = list(_basic_iter_dirs(base))
    if dirs:
        logging.info("Found %d top-level directories", len(dirs))
        with multiprocessing.Pool(processes=args.workers) as pool:
            for src, ok, msg in pool.imap_unordered(_basic_compress_dir, [(str(d), preset) for d in dirs]):
                (logging.info if ok else logging.error)("%s: %s", src, msg)
    else:
        logging.info("No top-level directories found")
    files = list(_basic_iter_files(base))
    if files:
        logging.info("Found %d top-level files", len(files))
        file_workers = max(1, multiprocessing.cpu_count() - 1)
        with multiprocessing.Pool(processes=file_workers) as pool:
            for src, ok, msg in pool.imap_unordered(_basic_compress_file, [(str(f), preset) for f in files]):
                (logging.info if ok else logging.error)("%s: %s", src, msg)
    else:
        logging.info("No top-level files found")
    logging.info("Done.")
    return 0


class NamedResult:
    def __init__(
        self,
        src: Optional[str] = None,
        dst: Optional[str] = None,
        ok: bool = False,
        error: Optional[str] = None,
    ) -> None:
        self.src = src
        self.dst = dst
        self.ok = ok
        self.error = error


def _named_iter_entries(base: Path, exclude_names: set):
    for p in base.iterdir():
        if p.name in exclude_names:
            continue
        if p.suffix in _NAMED_SKIP_SUFFIXES:
            continue
        yield p


def _named_remove(path: Path) -> None:
    if path.is_file() or path.is_symlink():
        path.unlink(missing_ok=True)
        return
    if path.is_dir():
        for child in path.iterdir():
            _named_remove(child)
        path.rmdir()


def _named_best_method():
    compressor = getattr(py7zr, "compressor", None)
    if compressor is None:
        return py7zr.FILTER_LZMA2
    for name in _NAMED_METHODS:
        if hasattr(compressor, name):
            return getattr(compressor, name)
    return py7zr.FILTER_LZMA2


def _named_compress_dir(path_str: str) -> NamedResult:
    path = Path(path_str)
    tar_path = path.parent / f"{path.name}.tar"
    try:
        if tar_path.exists():
            msg = f"{tar_path} exists"
            raise FileExistsError(msg)
        logging.info("Tar directory: %s -> %s", path, tar_path)
        with tarfile.open(tar_path, "w") as tar:
            tar.add(path, arcname=path.name)
        _named_remove(path)
        return NamedResult(str(path), str(tar_path), True)
    except Exception as exc:
        logging.exception("Directory failed: %s", path)
        return NamedResult(str(path), str(tar_path), False, str(exc))


def _named_compress_file(path_str: str) -> NamedResult:
    path = Path(path_str)
    archive_path = path.parent / f"{path.name}.7z"
    method = _named_best_method()
    try:
        if archive_path.exists():
            msg = f"{archive_path} exists"
            raise FileExistsError(msg)
        logging.info("Compress file: %s -> %s", path, archive_path)
        filters = [{"id": method, "preset": 9}]
        with py7zr.SevenZipFile(archive_path, mode="w", filters=filters) as archive:
            archive.write(path, arcname=path.name)
        _named_remove(path)
        return NamedResult(str(path), str(archive_path), True)
    except Exception as exc:
        logging.exception("File failed: %s", path)
        return NamedResult(str(path), str(archive_path), False, str(exc))


def run_named(args: argparse.Namespace) -> int:
    base = Path.cwd()
    log_file = base / args.log_file
    _basic_setup_logging(log_file)
    workers = max(1, multiprocessing.cpu_count() - 1)
    method = _named_best_method()
    logging.info("Base dir: %s", base)
    logging.info("Workers: %d", workers)
    logging.info("Best py7zr method: %s", method)
    exclude = {log_file.name}
    if "__file__" in globals():
        exclude.add(Path(__file__).name)
    entries = list(_named_iter_entries(base, exclude))
    dirs = [p for p in entries if p.is_dir()]
    files = [p for p in entries if p.is_file()]
    logging.info("Found %d dirs and %d files", len(dirs), len(files))
    results: list[NamedResult] = []
    if dirs:
        with multiprocessing.Pool(processes=min(workers, len(dirs))) as pool:
            results.extend(pool.map(_named_compress_dir, [str(d) for d in dirs]))
    if files:
        with multiprocessing.Pool(processes=min(workers, len(files))) as pool:
            results.extend(pool.map(_named_compress_file, [str(f) for f in files]))
    ok = sum(1 for r in results if r.ok)
    fail = len(results) - ok
    logging.info("Completed. success=%d fail=%d", ok, fail)
    for r in results:
        if not r.ok:
            logging.error("FAILED: %s -> %s | %s", r.src, r.dst, r.error)
    return 0


def _full_is_compressible(path: Path, min_size: int) -> bool:
    try:
        if not path.is_file() or path.is_symlink():
            return False
        if path.suffix in _FULL_SKIP_SUFFIXES:
            return False
        return path.stat().st_size >= min_size
    except (OSError, PermissionError):
        return False


def _full_list_files(base: Path, min_size: int, mode: str = "compress") -> list[Path]:
    if mode == "compress":
        return sorted(
            p for p in base.glob("*") if p.is_file() and not p.is_symlink() and _full_is_compressible(p, min_size)
        )
    return sorted(p for p in base.glob("*.7z") if p.is_file() and not p.is_symlink())


def _full_list_dirs(base: Path) -> list[Path]:
    return sorted(p for p in base.glob("*") if not p.is_symlink() and p.is_dir())


def _full_compress_inmem(src: Path, dst: Path) -> bool:
    try:
        data = src.read_bytes()
        if not data:
            return False
        tmp = Path(tempfile.mkstemp(suffix=".7z")[1])
        try:
            with py7zr.SevenZipFile(
                tmp,
                mode="w",
                filters=_FULL_SETTINGS["filters"],
                dictionary_size=_FULL_SETTINGS["dictionary_size"],
                solid=_FULL_SETTINGS["solid"],
                header_compression=_FULL_SETTINGS["header_compression"],
            ) as archive:
                archive.write(src, arcname=src.name)
            dst.write_bytes(tmp.read_bytes())
            return True
        finally:
            tmp.unlink(missing_ok=True)
    except Exception as exc:
        _log_error("Memory compression failed for {}: {}", src.name, exc)
        return False


def _full_compress_chunk(payload: tuple[bytes, int, str, int]) -> Optional[str]:
    chunk_bytes, index, temp_dir_str, preset = payload
    temp_dir = Path(temp_dir_str)
    bin_path = temp_dir / f"chunk_{index:06d}.bin"
    archive_path = temp_dir / f"chunk_{index:06d}.7z"
    try:
        bin_path.write_bytes(chunk_bytes)
        with py7zr.SevenZipFile(
            archive_path,
            mode="w",
            filters=[{"id": py7zr.FILTER_LZMA2, "preset": preset}],
        ) as archive:
            archive.write(bin_path, arcname=bin_path.name)
        return str(archive_path)
    finally:
        if bin_path.exists():
            bin_path.unlink()


def _full_compress_chunked(
    src: Path,
    dst: Path,
    size: int,
    chunk_size: int,
    workers: int,
) -> bool:
    temp_dir = Path(tempfile.gettempdir()) / "py7zr_temp" / f"compress_{src.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        num_chunks = (size + chunk_size - 1) // chunk_size
        payloads: list[tuple[bytes, int, str, int]] = []
        with src.open("rb") as fh, mmap.mmap(fh.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            for i in range(num_chunks):
                start = i * chunk_size
                end = min((i + 1) * chunk_size, size)
                payloads.append((mm[start:end], i, str(temp_dir), 9))
        chunk_paths: list[Optional[str]] = [None] * num_chunks
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for i, result in enumerate(pool.map(_full_compress_chunk, payloads)):
                chunk_paths[i] = result
        with py7zr.SevenZipFile(
            dst,
            mode="w",
            filters=_FULL_SETTINGS["filters"],
            dictionary_size=_FULL_SETTINGS["dictionary_size"],
            solid=_FULL_SETTINGS["solid"],
            header_compression=_FULL_SETTINGS["header_compression"],
        ) as archive:
            for chunk_path in chunk_paths:
                if chunk_path is not None:
                    cp = Path(chunk_path)
                    if cp.exists():
                        archive.write(cp, arcname=cp.name)
        return True
    except Exception as exc:
        _log_error("Chunked compression failed for {}: {}", src.name, exc)
        return False
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def _full_compress_dir(dir_path: Path, archive_path: Path) -> bool:
    try:
        with py7zr.SevenZipFile(
            archive_path,
            mode="w",
            filters=_FULL_SETTINGS["filters"],
            dictionary_size=_FULL_SETTINGS["dictionary_size"],
            solid=_FULL_SETTINGS["solid"],
            header_compression=_FULL_SETTINGS["header_compression"],
            recursive=True,
        ) as archive:
            archive.writeall(dir_path, arcname=dir_path.name)
        if not archive_path.exists():
            return False
        orig = sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file())
        comp = archive_path.stat().st_size
        if comp < orig:
            shutil.rmtree(dir_path)
            saved = (orig - comp) / orig * 100
            print(f"  ✓ Compressed archive: {saved:.1f}% saved ({_human_size(orig)} -> {_human_size(comp)})")
            return True
        _log_warning("  ✗ Archive compression didn't save space")
        archive_path.unlink()
        return False
    except Exception as exc:
        _log_error("Failed to compress folder {}: {}", dir_path.name, exc)
        if archive_path.exists():
            archive_path.unlink()
        return False


def _full_compress_file(
    src: Path,
    chunk_size: int,
    min_size: int,
    workers: int,
) -> tuple[bool, int, int]:
    dst = src.with_suffix(src.suffix + ".7z")
    if dst.exists():
        print(f"Skipping {src.name} - output already exists")
        return (False, 0, 0)
    try:
        size = src.stat().st_size
        if not size:
            return (False, 0, 0)
        if size < chunk_size:
            ok = _full_compress_inmem(src, dst)
        else:
            ok = _full_compress_chunked(src, dst, size, chunk_size, workers)
        if ok and dst.exists():
            comp = dst.stat().st_size
            if comp == 0:
                _log_warning("Compressed file empty for {}", src.name)
                dst.unlink()
                return (False, 0, 0)
            if comp < size:
                src.unlink()
                saved = (size - comp) / size * 100
                print(f"  ✓ {src.name}: {saved:.1f}% saved ({_human_size(size)} -> {_human_size(comp)})")
                return (True, size, comp)
            _log_warning("  ✗ {}: No space saved, removing compressed file", src.name)
            dst.unlink()
            return (False, 0, 0)
        return (False, 0, 0)
    except Exception as exc:
        _log_error("  ✗ Failed to compress {}: {}", src.name, exc)
        return (False, 0, 0)


def _full_decompress_one(archive: Path) -> tuple[bool, int, int]:
    out = archive.with_suffix("")
    try:
        with py7zr.SevenZipFile(archive, mode="r") as zf:
            comp_size = archive.stat().st_size
            if out.exists():
                _log_warning("  Output already exists, skipping...")
                return (False, 0, 0)
            zf.extractall(path=out)
            if out.is_file():
                decomp_size = out.stat().st_size
            else:
                decomp_size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
            print(f"  ✓ Decompressed {archive.name}: {_human_size(comp_size)} → {_human_size(decomp_size)}")
            archive.unlink()
            return (True, comp_size, decomp_size)
    except Exception as exc:
        _log_error("  ✗ Failed to decompress {}: {}", archive.name, exc)
        return (False, 0, 0)


def _full_compress(base: Path, args: argparse.Namespace) -> None:
    base.mkdir(parents=True, exist_ok=True)
    print("\n🔧 7-Zip Compression Settings:")
    print("   Format: 7z")
    print(f"   Filter: LZMA2 (preset {args.preset} - maximum)")
    print(f"   Dictionary size: {_FULL_SETTINGS['dictionary_size'] // (1024 * 1024)} MB")
    print("   Solid compression: Yes")
    print("   Header compression: Yes")
    print("   Block size: 4 MB")
    print(f"   Parallel workers: {args.workers}")
    print(f"   Chunk size: {_human_size(args.chunk_size)}")
    dirs = _full_list_dirs(base)
    if dirs:
        print(f"\n📁 Compressing {len(dirs)} directories...")
        for d in dirs:
            rel = d.relative_to(base)
            print(f"\n  Processing {rel}...")
            archive = d.parent / f"{d.name}.7z"
            if _full_compress_dir(d, archive):
                _log_info("  ✓ Successfully compressed {} to {}.7z", rel, d.name)
            else:
                _log_error("  ✗ Failed to compress {}", rel)
    files = _full_list_files(base, args.min_size, mode="compress")
    if not files:
        print("\n📄 No files to compress")
        return
    print(f"\n📄 Compressing {len(files)} files with 7-Zip max compression...")
    orig_total = comp_total = ok_count = 0
    for i, f in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] {f.name}")
        ok, orig, comp = _full_compress_file(f, args.chunk_size, args.min_size, args.workers)
        if ok:
            ok_count += 1
            orig_total += orig
            comp_total += comp
    if ok_count > 0:
        saved = orig_total - comp_total
        pct = saved / orig_total * 100 if orig_total else 0.0
        print("\n" + "=" * 40)
        print(f"✅ Compressed {ok_count}/{len(files)} files")
        print(f"📊 Original size: {_human_size(orig_total)}")
        print(f"📦 Compressed size: {_human_size(comp_total)}")
        print(f"💾 Space saved: {_human_size(saved)} ({pct:.1f}%)")
        print("=" * 40)
    elif files:
        _log_error("\n❌ No files were successfully compressed")


def _full_decompress(base: Path, args: argparse.Namespace) -> None:
    archives = _full_list_files(base, args.min_size, mode="decompress")
    if not archives:
        print("\n📄 No .7z files to decompress")
        return
    print(f"\n📄 Decompressing {len(archives)} 7-Zip archives...")
    comp_total = decomp_total = ok_count = 0
    for i, a in enumerate(archives, 1):
        print(f"\n[{i}/{len(archives)}] {a.name}")
        ok, comp, decomp = _full_decompress_one(a)
        if ok:
            ok_count += 1
            comp_total += comp
            decomp_total += decomp
    if ok_count > 0:
        print("\n" + "=" * 40)
        print(f"✅ Decompressed {ok_count}/{len(archives)} archives")
        print(f"📦 Compressed size: {_human_size(comp_total)}")
        print(f"📊 Decompressed size: {_human_size(decomp_total)}")
        print("=" * 40)
    elif archives:
        _log_error("\n❌ No files were successfully decompressed")


def run_full(args: argparse.Namespace) -> int:
    base = Path.cwd()
    if args.mode == "compress":
        _full_compress(base, args)
    else:
        _full_decompress(base, args)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merged 7-Zip compression tool")
    sub = parser.add_subparsers(dest="command", required=True)
    p_basic = sub.add_parser("basic", help="7zer.py: tar->7z dirs + 7z files")
    p_basic.add_argument("--log-file", default="compress.log")
    p_basic.add_argument("--workers", type=int, default=4)
    p_basic.add_argument("--preset", type=int, default=9)
    p_basic.set_defaults(func=run_basic)
    p_named = sub.add_parser("named", help="7zer2.py: dirs->tar, files->7z, best method")
    p_named.add_argument("--log-file", default="compress.log")
    p_named.set_defaults(func=run_named)
    p_full = sub.add_parser("full", help="7zr.py: full compress/decompress")
    p_full.add_argument(
        "--mode",
        choices=["compress", "decompress"],
        default="compress",
        help="Compress or decompress; matches the original -c/-d flags",
    )
    p_full.add_argument("--workers", type=int, default=8)
    p_full.add_argument("--chunk-size", type=int, default=524288)
    p_full.add_argument("--min-size", type=int, default=1024)
    p_full.add_argument("--preset", type=int, default=9)
    p_full.set_defaults(func=run_full)
    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        _log_warning("\n⚠️  Interrupted by user")
        return 1
    except Exception as exc:
        _log_error("\n❌ Unexpected error: {}", exc)
        return 1


if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
