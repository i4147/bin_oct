#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line utility for extracting a contiguous range of lines from a text file and saving them to a new file. The tool should accept three arguments: the path to a source file, a starting line number (1-based), and an optional ending line number. If the end line is omitted, the extraction should run from the start line through the last line of the file.
Key requirements:
- **Input validation:** Show a brief usage message to standard error and exit with a non-zero status if required arguments are missing. Verify that the start and end values are valid integers, that the start line is at least 1, and that the end line (when provided) is not less than the start line. Report clear error messages for each invalid case.
- **File handling:** Confirm that the specified source file exists before attempting to read it. If it does not, report an error and exit with a non-zero status. Read the source file as UTF-8 text, tolerating malformed bytes without crashing.
- **Output naming:** Automatically generate the output filename from the requested line range while preserving the original file's extension. When only a start line is given, the name should reflect just that line number; when a range is given, the name should reflect both the start and end numbers. Write the output file in the current working directory.
- **Extraction behavior:** Copy only the lines within the requested range, inclusive of both endpoints, into the output file. Handle cases where the requested range extends beyond the end of the file gracefully, and make sure the output reflects only the lines that actually exist.
- **Error handling:** Catch and report file system or encoding errors during reading or writing with informative messages on standard error, returning a non-zero exit code on failure. On success, exit with status zero.
- **Entry point:** Structure the script so it runs as a standalone program from the command line and returns an integer exit status to the operating system.
The deliverable is a single, self-contained, readable Python script that follows these behaviors and produces the extracted output file exactly as described.
---"""

from __future__ import annotations
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) < 3:
        print(
            f"""get from line X to Y of a file:
Usage: {sys.argv[0]} <filename> <start_line> [end_line]""",
            file=sys.stderr,
        )
        return 1
    filename = sys.argv[1]
    try:
        start = int(sys.argv[2])
        end = int(sys.argv[3]) if len(sys.argv) >= 4 else -1
    except ValueError:
        print("Error: start_line and end_line must be integers.", file=sys.stderr)
        return 1
    if start < 1 or (end != -1 and end < start):
        print("Invalid range: start must be >=1 and end >= start.", file=sys.stderr)
        return 1
    path = Path(filename)
    if not path.is_file():
        print("Error: Cannot open input file.", file=sys.stderr)
        return 1
    ext = path.suffix
    outname = f"{start}{ext}" if end == -1 else f"{start}_{end}{ext}"
    try:
        with (
            path.open("r", encoding="utf-8", errors="replace") as infile,
            Path(outname).open("w", encoding="utf-8") as outfile,
        ):
            for lineno, line in enumerate(infile, start=1):
                if lineno < start:
                    continue
                if end != -1 and lineno > end:
                    break
                outfile.write(line)
    except OSError:
        print("Error: Cannot create output file.", file=sys.stderr)
        return 1
    print(f"Saved to {outname}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
