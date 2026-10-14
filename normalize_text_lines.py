#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that normalizes the text content of a single UTF-8 file in place, line by line, so that each line becomes a canonicalized, lowercase, punctuation-free, underscore-joined token string suitable for comparison or indexing.
The script should accept exactly one command-line argument: the path to the input text file. If the argument is missing or extra arguments are supplied, it should print a brief usage message to standard error that shows the script name and expected argument, then exit with a non-zero status code.
For each line of the file, the script should:
- Remove the trailing line-ending characters while preserving the logical content of the line.
- Apply Unicode compatibility normalization so that visually equivalent characters (such as full-width and half-width forms or ligatures) are treated theard any non-printable or control characters.
- Remove all punctuation characters, using Unicode category rules rather than a hand-picked list.
- Convert the text to a case-insensitive, lowercase-comparable form.
- Collapse all runs of whitespace into single underscores, with no leading or trailing separators from the whitespace itself.
Each normalized line should be written back out with a single Unix-style newline character, so the output file uses consistent line endings regardless of the original file's format. Empty or fully-stripped lines should still produce an empty output line to preserve the original line count.
Safety and robustness requirements:
- The update must be atomic: write the result to a temporary file in the same directory as the input, then replace the original file only after the write completes successfully, so that a failure mid-process never leaves the original file corrupted or partially rewritten.
- Clean up the temporary file if an error occurs.
- Read and write using UTF-8 encoding.
- Report clear, human-readable error messages for common failures such as a missing file, permission problems, or invalid UTF-8 content, and exit with a non-zero status code.
The script should produce no output on success beyond what is necessary, and it should be runnable as a standalone command-line program.
---"""

from __future__ import annotations
from pathlib import Path
import sys
import tempfile
import unicodedata


def normalize_line(line: str) -> str:
    text = unicodedata.normalize("NFKC", line)
    text = "".join(char for char in text if char.isprintable())
    text = "".join(char for char in text if not unicodedata.category(char).startswith("P"))
    text = text.casefold()
    text = "_".join(text.split())
    return text


def normalize_file_in_place(path: Path) -> None:
    with (
        path.open("r", encoding="utf-8", newline="") as source,
        tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary,
    ):
        temporary_path = Path(temporary.name)
        for line in source:
            content = line.rstrip("\r\n")
            temporary.write(normalize_line(content) + "\n")
    temporary_path.replace(path)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} INPUT_FILE", file=sys.stderr)
        raise SystemExit(2)
    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f"Error: not a file: {input_path}", file=sys.stderr)
        raise SystemExit(1)
    try:
        normalize_file_in_place(input_path)
    except UnicodeDecodeError:
        print(
            f"Error: {input_path} is not valid UTF-8.",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
