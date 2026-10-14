#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that batch-compresses PDF files in a folder using Ghostscript to reduce their file sizes. The tool should accept a directory (or a set of PDF paths) as input, locate all PDF files within it, and process them concurrently using a small, bounded pool of worker threads so that several files are compressed in parallel without overwhelming the system.
For each PDF, the script should produce a downsampled, web/screen-optimized copy with the following behaviors:
- Recolor images to the sRGB color space and downsample color, grayscale, and monochrome images to a moderate resolution (around 85 DPI) using bicubic resampling.
- Target a PDF 1.4 compatibility level, subset embedded fonts, and optimize the output file, while not forcing all fonts to be embedded.
- Write the compressed result to a temporary file alongside the original, so the source is never corrupted during processing.
The script should report progress to the user in the console, printing for each file the size before compression and the size after compression, using human-readable units (KB, MB, etc.). It should also display the Ghostscript output so the user can see its progress or errors. After a successful run, the script should compare the original and compressed sizes and only replace the original file with the compressed version if the result is actually smaller; otherwise it should discard the temporary output and keep the original. Any temporary files must be cleaned up whether processing succeeds or fails, and a failure on one file should not stop the others from being processed.
At the end, the script should print a summary showing the total number of files processed, how many were reduced, and the overall space saved. It should accept its input location from the command line, print a usage message if arguments are missing or invalid, and exit with a clear error code on fatal problems such as a missing Ghostscript installation or an invalid input path.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import fsz, get_files, gsz, mpf, runcmd

MAX_WORKERS = 4


def process_file(path):
    path = Path(path)
    temp_gs = path.with_name(f"temp_gs_{path.name}")
    size_before = path.stat().st_size
    print(f"{path.name} Before : {fsz(size_before)}")
    gs_cmd = [
        "gs",
        "-dBATCH",
        "-dColorConversionStrategy=/sRGB",
        "-dColorImageDownsampleType=/Bicubic",
        "-dColorImageResolution=85",
        "-dCompatibilityLevel=1.4",
        "-dDownsampleColorImages=true",
        "-dDownsampleGrayImages=true",
        "-dDownsampleMonoImages=true",
        "-dEmbedAllFonts=false",
        "-dGrayImageDownsampleType=/Bicubic",
        "-dGrayImageResolution=85",
        "-dHaveTransparency=false",
        "-dMonoImageDownsampleType=/Bicubic",
        "-dMonoImageResolution=85",
        "-dNOPAUSE",
        "-dOptimize=true",
        "-dPDFSETTINGS=/screen",
        "-dSubsetFonts=true",
        "-sDEVICE=pdfwrite",
        f"-sOutputFile={temp_gs}",
        str(path),
    ]
    runcmd(gs_cmd, show_output=True)
    if temp_gs.exists():
        size_after = temp_gs.stat().st_size
        if size_after:
            print(f"{path.name} After  : {fsz(size_after)}")
            diff = size_before - size_after
            sign = "-" if diff >= 0 else "+"
            if size_after < size_before:
                temp_gs.replace(path)
                print(f"Saved  : {sign}{fsz(diff)}")
            else:
                print("original file is smaller")
                temp_gs.unlink(missing_ok=True)


def main():
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".pdf"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    mpf(process_file, files)
    after = gsz(cwd)
    dsz = before - after
    if dsz:
        print(f"space freed : {fsz(dsz)}")


if __name__ == "__main__":
    raise SystemExit(main())
