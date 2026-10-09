#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that spl or more large text files into smaller chunk files of at most 15,850 characters each, using a `dh.mpf_map` helper to apply the processing to multiple file paths (e.g., given via command-line arguments).
For each input file, read its UTF-8 text and repeatedly split it near the size limit, preferring to break at the last newline within the limit, falling back to the last whitespace, or otherwise cutting at the exact character count.
Write each resulting chunk to a new file in the same directory, reusing the original stem with a zero-padded numeric suffix (width based on the total chunk count, minimum 3 digits) appended before the extension, preserving UTF-8 encoding.
The script should skip empty files and catch and report any errors encountered while processing a given file without crashing the whole run."""

from __future__ import annotations
from pathlib import Path
import sys

from dh import mpf_map


CHUNKSIZE = 15_850


def split_at_boundary(text: str, max_size: int) -> tuple[str, str]:
    if len(text) <= max_size:
        return text, ""
    newline_pos = text.rfind("\n", 0, max_size + 1)
    if newline_pos > 0:
        split_pos = newline_pos + 1
        return text[:split_pos], text[split_pos:]
    whitespace_pos = -1
    for index in range(max_size, 0, -1):
        if text[index - 1].isspace():
            whitespace_pos = index
            break
    if whitespace_pos > 0:
        return text[:whitespace_pos], text[whitespace_pos:]
    return text[:max_size], text[max_size:]


def process_file(path: Path) -> None:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
        if not text:
            return
        remaining = text
        chunk_count = 0
        while remaining:
            chunk, remaining = split_at_boundary(remaining, CHUNKSIZE)
            chunk_count += 1
        padding_width = max(3, len(str(chunk_count - 1)))
        remaining = text
        part_num = 0
        while remaining:
            chunk, remaining = split_at_boundary(remaining, CHUNKSIZE)
            suffix = str(part_num).zfill(padding_width)
            outpath = path.with_stem(f"{path.stem}_{suffix}")
            outpath.write_text(chunk, encoding="utf-8")
            part_num += 1
    except Exception as error:
        print(f"An error occurred during file splitting: {error}")


def get_files(path: Path) -> list[Path]:
    return [
        file
        for file in path.rglob("*")
        if file.is_file() and not file.stem.endswith(tuple(f"_{number:03d}" for number in range(1000)))
    ]


def main() -> int:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files: list[Path] = []
    if args:
        for argument in args:
            path = Path(argument)
            if path.is_file():
                files.append(path)
            elif path.is_dir():
                files.extend(get_files(path))
    else:
        files = get_files(cwd)
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    elif files:
        mpf_map(process_file, files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
