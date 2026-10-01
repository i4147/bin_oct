#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that compresses PDF files using Ghostscript, invoked as a script operating on a target file or directory.
It should recursively discover PDFs via a `get_files` helper, and for each one run Ghostscript with a set of downsampling/compression flags, offering a `--fast` mode (partial-bound flag set using `/Subsample`, 70 DPI, font subsetting) versus a higher-quality default mode, executing the conversion via a `runcmd` helper.
The script should report original and compressed file sizes (using `fsz`/`gsz` helpers) for each processed file, optionally leveraging a multiprocessing map helper (`mpf`) to process multiple files in parallel up to `MAX_WORKERS`, and print a summary of space saved after processing completes."""

# ---------------------------------------------------------------------------
# Standard library imports.
# ---------------------------------------------------------------------------
import sys
from functools import partial  # lets us pre-bind the `fast` flag
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers from your `dh` module.
#   fsz   -> human readable file size
#   gsz   -> size of a folder (or file) in bytes
#   get_files -> discover files by extension
#   mpf   -> multiprocess map helper
#   runcmd -> run a shell command (list form), optionally showing output
# ---------------------------------------------------------------------------
from dh import fsz, get_files, gsz, mpf, runcmd

# ---------------------------------------------------------------------------
# Max number of parallel workers used by `mpf`. Currently unused because we
# don't know if your `dh.mpf` accepts a worker count — pass it in if it does.
# ---------------------------------------------------------------------------
MAX_WORKERS = 4
# ---------------------------------------------------------------------------
# Flag set used with `--fast`.
#   - Downsample color / gray / mono images
#   - Target 70 DPI on all three channels
#   - Use /Subsample (fastest, blocky) instead of /Average or /Bicubic
#   - Subset fonts, do not embed all fonts
# This produces smaller files faster, at the cost of some quality.
# ---------------------------------------------------------------------------
FAST_FLAGS = [
    "-dDownsampleColorImages=true",
    "-dDownsampleGrayImages=true",
    "-dDownsampleMonoImages=true",
    "-dColorImageResolution=70",
    "-dGrayImageResolution=70",
    "-dMonoImageResolution=70",
    "-dColorImageDownsampleType=/Subsample",
    "-dGrayImageDownsampleType=/Subsample",
    "-dMonoImageDownsampleType=/Subsample",
    "-dSubsetFonts=true",
    "-dEmbedAllFonts=false",
]
# ---------------------------------------------------------------------------
# Flag set used by default (no --fast).
#   - /screen preset already sets 72 DPI on color/gray, 300 on mono,
#     /Average downsample on color/gray, /Subsample on mono, font subsetting.
#   - We only add `-dMonoImageResolution=70` to push mono down from 300 -> 70.
# ---------------------------------------------------------------------------
SCREEN_FLAGS = [
    "-dPDFSETTINGS=/screen",
    "-dMonoImageResolution=70",
]


# ---------------------------------------------------------------------------
# Remove any leftover `temp_gs_*.tmp` files in the working directory.
# This catches temp files from a previous crashed / killed run so they don't
# accumulate. Your external cleaner script will also pick these up since
# they end with `.tmp`.
# ---------------------------------------------------------------------------
def cleanup_stale_temp(cwd: Path) -> None:
    for stale in cwd.glob("temp_gs_*.tmp"):
        try:
            stale.unlink()
            print(f"removed stale temp: {stale.name}")
        except OSError as e:
            print(f"could not remove {stale.name}: {e}")


# ---------------------------------------------------------------------------
# Shrink a single PDF.
#   path -> the PDF to shrink (overwritten in place if the result is smaller)
#   fast -> if True, use FAST_FLAGS; otherwise use SCREEN_FLAGS
#
# Ghostscript is told to write to a `.tmp` file so that:
#   1. We never clobber the original until we know the result is smaller.
#   2. If anything goes wrong (gs crash, ^C, kill), the `finally` block below
#      removes it, and your cleaner script will also remove it since it ends
#      with `.tmp`.
# ---------------------------------------------------------------------------
def process_file(path: Path, fast: bool = False) -> None:
    path = Path(path)
    # Temp file ends in `.tmp` so cleaner scripts can find/remove it.
    # For `foo.pdf` this becomes `temp_gs_foo.pdf.tmp`.
    temp_gs = path.with_name(f"temp_gs_{path.name}.tmp")
    # Pre-delete a leftover temp for this exact file, if any.
    if temp_gs.exists():
        temp_gs.unlink(missing_ok=True)
    size_before = path.stat().st_size
    print(f"{path.name} Before : {fsz(size_before)}")
    # Choose the flag set based on `fast`.
    extra = FAST_FLAGS if fast else SCREEN_FLAGS
    gs_cmd = [
        "gs",
        "-dBATCH",
        "-dNOPAUSE",
        "-sDEVICE=pdfwrite",
        *extra,  # expand chosen flag set
        f"-sOutputFile={temp_gs}",  # write to the .tmp file
        str(path),  # input file
    ]
    try:
        # Run Ghostscript. `show_output=True` streams gs stdout/stderr.
        runcmd(gs_cmd, show_output=True)
        # If gs produced nothing, bail out and keep the original.
        if not temp_gs.exists():
            print(f"{path.name}: gs produced no output, skipping")
            return
        size_after = temp_gs.stat().st_size
        # Empty output is never useful — keep the original.
        if not size_after:
            print(f"{path.name}: gs output is empty, keeping original")
            return
        print(f"{path.name} After  : {fsz(size_after)}")
        diff = size_before - size_after
        sign = "-" if diff >= 0 else "+"
        if size_after < size_before:
            # Replace original with the smaller temp file.
            # `replace` moves temp_gs -> path, so temp_gs no longer exists
            # and the `finally` block below is a no-op.
            temp_gs.replace(path)
            print(f"Saved  : {sign}{fsz(diff)}")
        else:
            # Original was already smaller; keep it and drop the temp.
            print("original file is smaller")
    finally:
        # Safety net: no matter how we exit (exception, ^C, early return),
        # remove the temp file if it still exists. `.tmp` suffix means a
        # cleaner script can also catch it if we somehow fail here.
        if temp_gs.exists():
            temp_gs.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Entry point.
#   * Parses `--fast` out of argv (can appear anywhere).
#   * Removes stale temp files from the current working directory.
#   * If file paths are given, processes those; otherwise processes every
#     `.pdf` in the cwd.
#   * Prints total space freed at the end.
# ---------------------------------------------------------------------------
def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    # `--fast` toggles the FASTA_FLAGS / SCREEN_FLAGS branch.
    fast = "--fast" in args
    args = [a for a in args if a != "--fast"]
    # Sweep leftover temp files from earlier runs.
    cleanup_stale_temp(cwd)
    before = gsz(cwd)  # total size of cwd before processing
    # If the user passed file paths, use them; otherwise auto-discover pdfs.
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".pdf"])
    if not files:
        print("no pdf files found")
        return
    # Single-file fast path — avoids mpf overhead.
    if len(files) == 1:
        process_file(files[0], fast=fast)
        after = gsz(cwd)
        dsz = before - after
        if dsz:
            print(f"space freed : {fsz(dsz)}")
        return
    # Multi-file path — parallel map with `fast` pre-bound.
    # If `dh.mpf` supports a worker count, pass `MAX_WORKERS` here.
    mpf(partial(process_file, fast=fast), files)
    after = gsz(cwd)
    dsz = before - after
    if dsz:
        print(f"space freed : {fsz(dsz)}")


if __name__ == "__main__":
    raise SystemExit(main())
