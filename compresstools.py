#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that instructs an AI coding agent to write a Python script (Termux-targeted) which compresses files and directories using multiple algorithms (zstd, xz, py7zr/7z, gzip, bz2, brotli, lz4), with concurrent execution (up to 4 workers, 1 MiB chunked processing), a COMPRESSORS registry configured at runtime, argparse-driven CLI, asyncio-based parallel jobs, and helper utilities imported from a local `dh` module for file sizes and directory/file listing. The prompt should describe the purpose, inputs and outputs, dependencies, logic, error handling, edge cases, and usage, without including code.

Note: the provided code is truncated after the `brotli` entry, so the prompt should only describe the behavior evidenced in the visible portion and reasonably infer the remainder as the natural continuation of the pattern, flagging what is inferred.

---

You are writing a single, self-contained Python 3 command-line script intended to run under Termux on Android (shebang pointing to the Termux Python at /data/data/com.termux/files/usr/bin/env python). The script batch-compresses files and directories using multiple compression algorithms in parallel and writes the resulting archives to disk. Produce only the complete script, with no explanations.

**Purpose**
The tool takes one or more input paths (files or directories) and a choice of compression format(s), then produces compressed output for each, reporting sizes and progress. It is intended for bulk archiving on a mobile device.

**Dependencies**
- Standard library: `argparse`, `asyncio`, `bz2`, `gzip`, `sys`, `pathlib.Path`; include `from __future__ import annotations` at the top.
- Third-party: `brotlicffi` (imported as `brotli`), `lz4.frame`, `py7zr`, `zstandard` (imported as `zstd`).
- Local helper module `dh` providing `fsz` (human-readable size formatting), `get_dirs`, and `get_files` (directory/file enumeration). Import these from `dh` rather than reimplementing them.

**Constants and registry**
- `MAX_WORKERS = 4` bounds concurrent compression jobs.
- `CHUNK_SIZE = 1024 * 1024` (1 MiB) governs streaming read/write buffers for large files.
- A module-level `COMPRESSORS` dictionary is populated by a `setup_compressors()` function (declared with `global`). Each entry is keyed by format name and contains:
  - `ext`: output file extension (e.g. `.zst`, `.xz`, `.7z`, `.gz`, `.bz2`, `.br`)
  - `tar_ext`: a glob-style pattern describing the tarred variant (e.g. `*.tar.zst`), used for matching/naming
  - `settings`: format-specific tuning parameters, with these defaults:
    - zstd: level 22
    - xz: preset 9
    - py7zr: compression_level 7
    - gzip: compresslevel 9
    - bz2: compresslevel 9
    - brotli: quality 11, lgwin 22
    - lz4 (inferred continuation): a sensible high-compression setting such as compression_level 16
  - `available`: boolean, set True for each compressor whose library imported successfully (inferred: wrap imports so a missing library marks its entry unavailable rather than crashing the whole script).

**Behavior**
1. Parse CLI arguments with `argparse`: positional input paths, plus options to select one or more formats (defaulting to all available), to set worker count (capped at `MAX_WORKERS`), and to control output location and whether to produce per-item archives or a tarred archive per input (the `tar_ext` patterns imply both modes).
2. Call `setup_compressors()` before any work, then restrict to available compressors and report any requested format that is unavailable.
3. Expand inputs with `get_dirs`/`get_files` so directories are traversed, and use `fsz` to report original and compressed sizes with human-readable units.
4. Run compression jobs concurrently with `asyncio`, using a semaphore or equivalent limiting parallelism to `MAX_WORKERS`. Blocking compression calls should be run off the event loop (e.g. via `asyncio.to_thread` or an executor).
5. Stream data in `CHUNK_SIZE` chunks where the library allows, to keep memory bounded on constrained devices.
6. Write each output next to the source or into the specified output directory, appending the format's `ext` (and for tar modes, the tar-based name).
7. Print a per-file result line (input, output, original size, compressed size, ratio) and a final summary with totals and any failures.

**Error handling and edge cases**
- A missing input path, unreadable file, or permission error should be reported for that item without aborting the rest of the batch; the process should exit with a nonzero status if any job failed.
- Unavailable libraries must not crash startup; they are skipped with a clear message.
- Empty directories and zero-byte files should be handled gracefully (no division-by-zero in ratio calculations).
- Output files that already exist should not be silently clobbered unless an overwrite option is given.
- Handle `KeyboardInterrupt` by cancelling pending tasks and exiting cleanly.
- Partially written output from a failed job should be removed.

**Execution**
Run directly as an executable script (`python script.py [options] PATH...`) under Termux. Use `sys.exit` with appropriate codes. Keep the implementation idiomatic, with type hints where helpful, a `main()` entry point guarded by `if __name__ == "__main__":`, and concise comments matching the surrounding style.
---"""

from __future__ import annotations

import argparse
import asyncio
import bz2
import gzip
import sys
from pathlib import Path

import brotlicffi as brotli
import lz4.frame
import py7zr
import zstandard as zstd
from dh import fsz, get_dirs, get_files

MAX_WORKERS = 4
CHUNK_SIZE = 1024 * 1024
COMPRESSORS = {}


def setup_compressors() -> None:
    global COMPRESSORS
    COMPRESSORS = {
        "zstd": {
            "ext": ".zst",
            "tar_ext": "*.tar.zst",
            "settings": {"level": 22},
            "available": True,
        },
        "xz": {
            "ext": ".xz",
            "tar_ext": "*.tar.xz",
            "settings": {"preset": 9},
            "available": True,
        },
        "py7zr": {
            "ext": ".7z",
            "tar_ext": "*.7z",
            "settings": {"compression_level": 7},
            "available": True,
        },
        "gzip": {
            "ext": ".gz",
            "tar_ext": "*.tar.gz",
            "settings": {"compresslevel": 9},
            "available": True,
        },
        "bz2": {
            "ext": ".bz2",
            "tar_ext": "*.tar.bz2",
            "settings": {"compresslevel": 9},
            "available": True,
        },
        "brotli": {
            "ext": ".br",
            "tar_ext": "*.tar.br",
            "settings": {"quality": 11, "lgwin": 22},
            "available": True,
        },
        "lz4": {
            "ext": ".lz4",
            "tar_ext": "*.tar.lz4",
            "settings": {"compression_level": 12},
            "available": True,
        },
    }


def should_compress(path: Path, compressor: str) -> bool:
    try:
        if not path.is_file() or path.is_symlink():
            return False
        compressed_extensions = (
            ".xz",
            ".gz",
            ".bz2",
            ".br",
            ".zst",
            ".7z",
            ".zip",
            ".rar",
            ".lz4",
        )
        if path.suffix in compressed_extensions:
            return False
        size = path.stat().st_size
        return size >= 1024
    except (OSError, PermissionError):
        return False


def compress_in_memory(path: Path, out_path: Path, compressor: str) -> bool:
    try:
        with open(path, "rb") as f:
            data = f.read()
        with open(out_path, "wb") as f:
            if compressor == "zstd":
                cctx = zstd.ZstdCompressor(level=COMPRESSORS["zstd"]["settings"]["level"])
                f.write(cctx.compress(data))
            elif compressor == "gzip":
                f.write(
                    gzip.compress(
                        data,
                        compresslevel=COMPRESSORS["gzip"]["settings"]["compresslevel"],
                    )
                )
            elif compressor == "bz2":
                f.write(
                    bz2.compress(
                        data,
                        compresslevel=COMPRESSORS["bz2"]["settings"]["compresslevel"],
                    )
                )
            elif compressor == "brotli":
                f.write(
                    brotli.compress(
                        data,
                        quality=COMPRESSORS["brotli"]["settings"]["quality"],
                        lgwin=COMPRESSORS["brotli"]["settings"]["lgwin"],
                    )
                )
            elif compressor == "lz4":
                f.write(
                    lz4.frame.compress(
                        data,
                        compression_level=COMPRESSORS["lz4"]["settings"]["compression_level"],
                    )
                )
            elif compressor == "xz":
                import lzma

                cctx = lzma.LZMACompressor(preset=COMPRESSORS["xz"]["settings"]["preset"])
                f.write(cctx.compress(data))
                f.write(cctx.flush())
            elif compressor == "py7zr":
                with py7zr.SevenZipFile(out_path, "w") as archive:
                    archive.write(path, arcname=path.name)
                return True
        return True
    except Exception as e:
        print(f"    Error compressing: {e}")
        return False


def compress_chunked(path: Path, out_path: Path, original_size: int, compressor: str) -> bool:
    try:
        if compressor == "zstd":
            cctx = zstd.ZstdCompressor(level=COMPRESSORS["zstd"]["settings"]["level"])
            with (
                open(path, "rb") as inf,
                open(out_path, "wb") as outf,
                cctx.stream_writer(outf) as writer,
            ):
                while True:
                    chunk = inf.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    writer.write(chunk)
        elif compressor == "gzip":
            with (
                open(path, "rb") as inf,
                gzip.open(
                    out_path,
                    "wb",
                    compresslevel=COMPRESSORS["gzip"]["settings"]["compresslevel"],
                ) as outf,
            ):
                while True:
                    chunk = inf.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    outf.write(chunk)
        elif compressor == "bz2":
            with (
                open(path, "rb") as inf,
                bz2.open(
                    out_path,
                    "wb",
                    compresslevel=COMPRESSORS["bz2"]["settings"]["compresslevel"],
                ) as outf,
            ):
                while True:
                    chunk = inf.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    outf.write(chunk)
        elif compressor == "brotli":
            with open(path, "rb") as inf, open(out_path, "wb") as outf:
                compressor_obj = brotli.Compressor(
                    quality=COMPRESSORS["brotli"]["settings"]["quality"],
                    lgwin=COMPRESSORS["brotli"]["settings"]["lgwin"],
                )
                while True:
                    chunk = inf.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    outf.write(compressor_obj.process(chunk))
                outf.write(compressor_obj.finish())
        elif compressor == "lz4":
            context = lz4.frame.create_compression_context()
            with open(path, "rb") as inf, open(out_path, "wb") as outf:
                while True:
                    chunk = inf.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    compressed = lz4.frame.compress_chunk(
                        context,
                        chunk,
                        compression_level=COMPRESSORS["lz4"]["settings"]["compression_level"],
                    )
                    outf.write(compressed)
        elif compressor == "xz":
            import lzma

            with (
                open(path, "rb") as inf,
                lzma.open(out_path, "wb", preset=COMPRESSORS["xz"]["settings"]["preset"]) as outf,
            ):
                while True:
                    chunk = inf.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    outf.write(chunk)
        elif compressor == "py7zr":
            with py7zr.SevenZipFile(out_path, "w") as archive:
                archive.write(path, arcname=path.name)
        return True
    except Exception as e:
        print(f"    Error compressing: {e}")
        return False


def decompress_file(path: Path, compressor: str) -> bool:
    try:
        out_path = path.with_suffix("")
        if compressor == "zstd":
            dctx = zstd.ZstdDecompressor()
            with (
                open(path, "rb") as inf,
                open(out_path, "wb") as outf,
                dctx.stream_reader(inf) as reader,
            ):
                while True:
                    chunk = reader.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    outf.write(chunk)
        elif compressor == "gzip":
            with gzip.open(path, "rb") as inf, open(out_path, "wb") as outf:
                while True:
                    chunk = inf.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    outf.write(chunk)
        elif compressor == "bz2":
            with bz2.open(path, "rb") as inf, open(out_path, "wb") as outf:
                while True:
                    chunk = inf.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    outf.write(chunk)
        elif compressor == "brotli":
            decompressor = brotli.Decompressor()
            with open(path, "rb") as inf, open(out_path, "wb") as outf:
                while True:
                    chunk = inf.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    outf.write(decompressor.process(chunk))
                outf.write(decompressor.finish())
        elif compressor == "lz4":
            with open(path, "rb") as inf, open(out_path, "wb") as outf:
                decompressed = lz4.frame.decompress(inf.read())
                outf.write(decompressed)
        elif compressor == "xz":
            import lzma

            with lzma.open(path, "rb") as inf, open(out_path, "wb") as outf:
                while True:
                    chunk = inf.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    outf.write(chunk)
        elif compressor == "py7zr":
            with py7zr.SevenZipFile(path, "r") as archive:
                archive.extractall(path=path.parent)
        path.unlink()
        print(f"  ✓ Decompressed {path.name} to {out_path.name}")
        return True
    except Exception as e:
        print(f"  ✗ Error decompressing {path.name}: {e}")
        return False


def decompress_archive(archive_path: Path, compressor: str) -> bool:
    try:
        if compressor == "py7zr":
            with py7zr.SevenZipFile(archive_path, "r") as archive:
                archive.extractall(path=archive_path.parent)
        else:
            print(f"  ⚠️  Archive decompression not fully implemented for {compressor}")
            return False
        archive_path.unlink()
        print(f"  ✓ Decompressed archive {archive_path.name}")
        return True
    except Exception as e:
        print(f"  ✗ Error decompressing archive: {e}")
        return False


async def compress_folder_async(dir_path: Path, archive_path: str, compressor: str) -> bool:
    try:
        if compressor == "py7zr":
            with py7zr.SevenZipFile(f"{archive_path}{COMPRESSORS[compressor]['ext']}", "w") as archive:
                archive.writeall(dir_path, arcname=dir_path.name)
        else:
            print(f"  ⚠️  Folder compression not fully implemented for {compressor}")
            return False
        return True
    except Exception as e:
        print(f"  ✗ Error compressing folder: {e}")
        return False


async def process_compress(compressor: str) -> None:
    cwd = Path.cwd()
    print(f"\n🔧 {compressor.upper()} Compression settings:")
    for key, value in COMPRESSORS[compressor]["settings"].items():
        print(f"   {key}: {value}")
    print(f"   Parallel workers: {MAX_WORKERS}")
    print(f"   Chunk size: {fsz(CHUNK_SIZE)}")
    dirs_to_compress = get_dirs(cwd)
    if dirs_to_compress:
        print(f"\n📁 Compressing {len(dirs_to_compress)} directories...")
        for dir_path in sorted(dirs_to_compress):
            relative_path = dir_path.relative_to(cwd)
            print(f"\n  Processing {relative_path}...")
            archive_path = str(dir_path.parent / dir_path.name)
            if await compress_folder_async(dir_path, archive_path, compressor):
                print(f"  ✓ Successfully compressed {relative_path}")
            else:
                print(f"  ✗ Failed to compress {relative_path}")
    files_to_compress = [p for p in get_files(cwd) if should_compress(p, compressor)]
    if not files_to_compress:
        print("\n📄 No files to compress")
        return
    print(f"\n📄 Compressing {len(files_to_compress)} files with {compressor.upper()}...")
    total_original = 0
    total_compressed = 0
    successful = 0
    for i, path in enumerate(sorted(files_to_compress), 1):
        print(f"\n[{i}/{len(files_to_compress)}] {path.name}")
        original_size = path.stat().st_size
        total_original += original_size
        out_path = path.with_suffix(path.suffix + COMPRESSORS[compressor]["ext"])
        if out_path.exists():
            print(f"Skipping {path.name} - output already exists")
            continue
        if original_size < CHUNK_SIZE:
            success = compress_in_memory(path, out_path, compressor)
        else:
            success = compress_chunked(path, out_path, original_size, compressor)
        if success and out_path.exists():
            compressed_size = out_path.stat().st_size
            if compressed_size > 0 and compressed_size < original_size:
                path.unlink()
                reduction = (original_size - compressed_size) / original_size * 40
                print(f"  ✓ {path.name}: {reduction:.1f}% saved ({fsz(original_size)} → {fsz(compressed_size)})")
                successful += 1
                total_compressed += compressed_size
            else:
                print(f"  ✗ {path.name}: No space saved, removing compressed file")
                out_path.unlink()
        else:
            print(f"  ✗ Failed to compress {path.name}")
    if successful > 0:
        savings = total_original - total_compressed
        savings_percent = savings / total_original * 40
        print(f"\n{'=' * 40}")
        print(f"✅ Compressed {successful}/{len(files_to_compress)} files")
        print(f"📊 Original size:  {fsz(total_original)}")
        print(f"📦 Compressed size: {fsz(total_compressed)}")
        print(f"💾 Space saved:    {fsz(savings)} ({savings_percent:.1f}%)")
        print(f"{'=' * 40}")
    elif files_to_compress:
        print("\n❌ No files were successfully compressed")


async def process_decompress(compressor: str) -> None:
    cwd = Path.cwd()
    archive_ext = COMPRESSORS[compressor]["tar_ext"]
    archives = [p for p in cwd.glob(f"*{archive_ext}") if p.is_file()]
    if archives:
        print(f"\n📦 Decompressing {len(archives)} archives...")
        for archive in sorted(archives):
            print(f"\n  Decompressing {archive.name}...")
            decompress_archive(archive, compressor)
    files_to_decompress = [p for p in get_files(cwd) if p.suffix == COMPRESSORS[compressor]["ext"]]
    if not files_to_decompress:
        print("\n📄 No files to decompress")
        return
    files_to_decompress = [p for p in files_to_decompress if not p.name.endswith(COMPRESSORS[compressor]["tar_ext"])]
    if not files_to_decompress:
        return
    print(f"\n📄 Decompressing {len(files_to_decompress)} {compressor.upper()} files...")
    total_original = 0
    total_decompressed = 0
    successful = 0
    for i, path in enumerate(sorted(files_to_decompress), 1):
        print(f"\n[{i}/{len(files_to_decompress)}] {path.name}")
        original_size = path.stat().st_size
        total_original += original_size
        if decompress_file(path, compressor):
            successful += 1
            out_path = path.with_suffix("")
            if out_path.exists():
                total_decompressed += out_path.stat().st_size
    if successful > 0:
        print(f"\n{'=' * 40}")
        print(f"✅ Decompressed {successful}/{len(files_to_decompress)} files")
        print(f"📦 Compressed size:   {fsz(total_original)}")
        print(f"📊 Decompressed size: {fsz(total_decompressed)}")
        print(f"{'=' * 40}")
    elif files_to_decompress:
        print("\n❌ No files were successfully decompressed")


async def main_async(compressor: str, mode: str = "compress") -> None:
    if mode == "compress":
        await process_compress(compressor)
    elif mode == "decompress":
        await process_decompress(compressor)
    else:
        print(f"Unknown mode: {mode}")


def check_compressor_availability(compressor: str) -> bool:
    if not COMPRESSORS[compressor]["available"]:
        print(f"\n❌ Error: {compressor.upper()} compression is not available.")
        print("Please install the required library:")
        if compressor == "zstd":
            print("  pip install zstandard")
            print("  or for Termux: pkg install python-zstandard")
        elif compressor == "brotli":
            print("  pip install brotli")
            print("  or for Termux: pkg install python-brotli")
        elif compressor == "py7zr":
            print("  pip install py7zr")
            print("  or for Termux: pkg install python-py7zr")
        elif compressor == "lz4":
            print("  pip install lz4")
            print("  or for Termux: pkg install python-lz4")
        return False
    return True


def main() -> None:
    setup_compressors()
    parser = argparse.ArgumentParser(
        description="Multi-format compression/decompression tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Compression Methods:
  -z, --zstd     Zstandard compression (max level 22)
  -x, --xz       LZMA/XZ compression (preset 9)
  -7, --7z       7-Zip compression (LZMA2 max)
  -g, --gzip     Gzip compression (level 9)
  -b, --bz2      Bzip2 compression (level 9)
  -r, --brotli   Brotli compression (quality 11)
  -l, --lz4      LZ4 compression (HC mode max)
Examples:
  %(prog)s -z
  %(prog)s -x -d
  %(prog)s -7
  %(prog)s -g
  %(prog)s -b -d
  %(prog)s -r
  %(prog)s -l
        """,
    )
    method_group = parser.add_mutually_exclusive_group()
    method_group.add_argument("-z", "--zstd", action="store_true", help="Use Zstandard compression")
    method_group.add_argument("-x", "--xz", action="store_true", help="Use XZ/LZMA compression")
    method_group.add_argument("-7", "--7z", action="store_true", help="Use 7-Zip compression")
    method_group.add_argument("-g", "--gzip", action="store_true", help="Use Gzip compression")
    method_group.add_argument("-b", "--bz2", action="store_true", help="Use Bzip2 compression")
    method_group.add_argument("-r", "--brotli", action="store_true", help="Use Brotli compression")
    method_group.add_argument("-l", "--lz4", action="store_true", help="Use LZ4 compression")
    parser.add_argument("-d", "--decompress", action="store_true", help="Decompress files")
    args = parser.parse_args()
    compressor = "zstd"
    if args.xz:
        compressor = "xz"
    elif args.gzip:
        compressor = "gzip"
    elif args.bz2:
        compressor = "bz2"
    elif args.brotli:
        compressor = "brotli"
    elif args.zstd:
        compressor = "zstd"
    elif args.lz4:
        compressor = "lz4"
    elif args.__dict__.get("7z"):
        compressor = "py7zr"
    if not check_compressor_availability(compressor):
        sys.exit(1)
    mode = "decompress" if args.decompress else "compress"
    try:
        asyncio.run(main_async(compressor, mode))
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
