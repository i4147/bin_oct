#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that splits a text file into a specified number of roughly equal parts, saving each part as a separate new file alongside the original.
The tool should accept two inputs: the path to a source file and a positive integer indicating how many parts to produce. Before splitting, it must check whether the file is binary; if so, it should print a clear error message to the error output stream and exit with a non-zero status without creating any files. The file should be read as UTF-8 text, and the split should be made by lines, so that each part contains complete lines only and the content of all parts, concatenated in order, reproduces the original file exactly.
Each output file should be named after the original file's base name with a zero-padded sequence number inserted before the original extension (for example, a file named report.txt split into three parts yields report_1.txt, report_2.txt, report_3.txt, with the padding width matching the number of digits in the requested part count). All output files should be written to the same directory as the source file, and the tool should report each created file's path to standard output as it is written.
Distribute lines as evenly as possible across parts; any remainder lines should be absorbed by the final part. The tool must reject a part count that is zero or negative by raising a clear error with a descriptive message. If the number of requested parts exceeds the number of lines in the file, the behavior should be handled gracefully, and the tool should not crash. Provide a command-line entry point that validates its arguments, prints concise usage guidance when arguments are missing or malformed, and exits cleanly on success or failure.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import is_binary


def split_file_into_parts(path: Path, n: int) -> None:
    if n <= 0:
        msg = "n must be a positive integer"
        raise ValueError(msg)
    if is_binary(path):
        print(f"Error: binary file '{path}' detected. Aborting.", file=sys.stderr)
        sys.exit(1)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    num_lines = len(lines)
    padding_width = len(str(n))
    base = num_lines // n
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    start = 0
    for i in range(1, n + 1):
        if i == n:
            end = num_lines
        else:
            end = start + base
        index_str = str(i).zfill(padding_width)
        part_name = f"{stem}_{index_str}{suffix}"
        part_path = parent / part_name
        part_path.write_text("".join(lines[start:end]), encoding="utf-8")
        print(f"Created: {part_path}")
        start = end


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python script.py <n> <path>")
        sys.exit(1)
    try:
        path = Path(sys.argv[1])
        n = int(sys.argv[2])
    except ValueError:
        print("Error: n must be an integer.", file=sys.stderr)
        sys.exit(1)
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    split_file_into_parts(path, n)


if __name__ == "__main__":
    raise SystemExit(main())
