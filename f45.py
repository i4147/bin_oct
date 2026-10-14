#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that wraps the contents of a plain text file so that it fits neatly within the current terminal width. The tool should accept a file path from the command line, read the file's text, and reflow each paragraph so that no line exceeds the available terminal columns, while preserving the original paragraph structure (blank lines separating paragraphs should remain). Long words should not be broken mid-word, and hyphenated words should not be split at hyphens. Lines that are already empty should stay empty. The wrapped result should be printed to standard output by default, so it can be piped or redirected, and the tool should also offer an option to write the result back to the original file or to a specified output file. Determine the target width automatically from the terminal size, with a sensible fallback when the size cannot be detected, and allow the user to override the width with a command-line option. The script should provide clear help text describing its usage, handle common errors gracefully (such as a missing or unreadable file, or an invalid width value) with informative messages and non-zero exit codes, and use a consistent UTF-8 text encoding for reading and writing.
---"""

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
