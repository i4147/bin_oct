#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a text file and splits its contents into chunks of a fixed maximum size, preferring to break at natural boundaries so that no chunk cuts a line or word in the middle when avoidable. The script should accept one or more file paths (for example from the command line), process each file independently, and report for each file how many chunks it was divided into. It should handle files gracefully: skip empty files, handle missing or unreadable files with a clear error message without stopping the processing of other files, and read and write text using UTF-8 encoding. The chunking logic should first try to break at the last newline within the size limit, then fall back to the last whitespace character, and only as a last resort split at the exact size limit. The script should write each chunk to its own output file, named systematically from the original file name with a zero-padded sequence number whose width adapts to the total number of chunks, so that files sort correctly. Include a clear usage message when run without arguments, and make the maximum chunk size a configurable constant that is easy to change.
---"""

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
