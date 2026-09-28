#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python cleanup script that scans all files in the current working directory using helper functions `get_files` and `is_binary` from a local `dh` module, skipping and reporting any binary files it encounters.
For each remaining text file, it reads the content with UTF-8 encoding and deletes the file if its total character length is below 100 or its line count is below 3, printing a removal message for each deleted file.
It should be structured with a `process_file` function that validates the path exists before processing, and a `main` function that orchestrates iteration over the discovered files, exiting via `SystemExit` when run as a script."""

from pathlib import Path
from dh import get_files, is_binary

SIZE_THRESHOLD = 100
LINE_THRESHOLD = 3


def process_file(path: Path) -> None:
    path = Path(path)
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")
    number_of_lines = len(content.splitlines())
    if len(content) < SIZE_THRESHOLD or number_of_lines < LINE_THRESHOLD:
        del content, number_of_lines
        path.unlink()
        print(f"{path.name} removed")


def main() -> None:
    cwd = Path.cwd()
    files = get_files(cwd)
    for path in files:
        if is_binary(path):
            print(f"{path.name} is binary")
            continue
        process_file(path)


if __name__ == "__main__":
    raise SystemExit(main())
