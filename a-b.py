#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line script that removes lines from a first text file if they also appear as lines in a second text file.
The script takes two file paths as command-line arguments: the file to filter and the file containing lines to exclude.
It reads all lines from the second file into a set for comparison, then filters the first file's lines, keeping only those not present in that set.
The filtered content is written to a temporary file with a ".tmp" suffix and then atomically renamed to overwrite the original first file, ensuring the first file is safely modified in place."""

import sys
from pathlib import Path


def main() -> None:
    file_a = Path(sys.argv[1])
    file_b = Path(sys.argv[2])
    b_lines = {
        line.rstrip("\n") for line in file_b.read_text(encoding="utf-8").splitlines()
    }
    a_lines = file_a.read_text(encoding="utf-8").splitlines(keepends=True)
    kept_lines = [line for line in a_lines if line.rstrip("\n") not in b_lines]
    tmp_path = file_a.with_suffix(file_a.suffix + ".tmp")
    tmp_path.write_text("".join(kept_lines), encoding="utf-8")
    tmp_path.replace(file_a)


if __name__ == "__main__":
    raise SystemExit(main())
