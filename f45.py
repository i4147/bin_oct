#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that reads a text file and rewraps its content so each line fits within a given width, preserving paragraph breaks (splitting on blank lines) while leaving empty lines untouched.
It should use argparse to accept a file path, an optional "-i/--inplace" flag to overwrite the original file instead of printing to stdout, and an optional "-w/--width" argument to override the wrap width, defaulting to the current terminal width when not specified.
The wrapping logic should use textwrap.fill per line with break_long_words and break_on_hyphens disabled, then rejoin wrapped lines and paragraphs, and the script should handle file reading/writing and output appropriately based on the in-place flag."""

from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys
import textwrap


def wrap_text_content(content: str, width: int) -> str:
    paragraphs = content.split("\n\n")
    wrapped_paragraphs = []
    for paragraph in paragraphs:
        lines = paragraph.splitlines()
        if not lines:
            wrapped_paragraphs.append("")
            continue
        wrapped_lines = []
        for line in lines:
            if not line.strip():
                wrapped_lines.append("")
                continue
            wrapped = textwrap.fill(
                line,
                width=width,
                break_long_words=False,
                break_on_hyphens=False,
                replace_whitespace=False,
                drop_whitespace=True,
            )
            wrapped_lines.append(wrapped)
        wrapped_paragraphs.append("\n".join(wrapped_lines))
    return "\n\n".join(wrapped_paragraphs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Wrap text file content to match terminal width.")
    parser.add_argument("file", type=Path, help="Path to the target file")
    parser.add_argument(
        "-i",
        "--inplace",
        action="store_true",
        help="Modify the original file in-place",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=None,
        help="Override target wrapping width (defaults to current terminal width)",
    )
    args = parser.parse_args()
    file_path: Path = args.file
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    if file_path.is_dir():
        print(f"Error: '{file_path}' is a directory.", file=sys.stderr)
        sys.exit(1)
    if args.width:
        width = max(args.width, 20)
    else:
        columns = shutil.get_terminal_size().columns
        width = max(columns, 20)
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    wrapped_content = wrap_text_content(content, width)
    if args.inplace:
        output_path = file_path
    else:
        output_path = file_path.with_name(f"{file_path.stem}_wrapped{file_path.suffix}")
    try:
        output_path.write_text(wrapped_content + "\n", encoding="utf-8")
        print(f"Successfully wrote wrapped text ({width} cols) to '{output_path}'.")
    except Exception as e:
        print(f"Error writing file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
