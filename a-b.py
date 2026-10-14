#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes two text file paths from the command line: a primary file and a reference file. The script should remove from the primary file every line whose content matches any line appearing in the reference file, while preserving all other lines exactly as they are, including their original line endings. Comparison should ignore trailing newline characters only; all other characters, including leading whitespace and trailing spaces, must be compared exactly. Both files should be read and written using UTF-8 encoding.
The script must update the primary file in place in a safe manner: write the filtered content to a temporary file alongside the original, then replace the original with it so that a failure partway through does not corrupt the primary file. The script should exit cleanly on success and return a zero status code. It should accept exactly two positional arguments and run only when executed directly, not when imported as a module.
---"""

from __future__ import annotations
from pathlib import Path
import sys


def main() -> None:
    file_a = Path(sys.argv[1])
    file_b = Path(sys.argv[2])
    b_lines = {line.rstrip("\n") for line in file_b.read_text(encoding="utf-8").splitlines()}
    a_lines = file_a.read_text(encoding="utf-8").splitlines(keepends=True)
    kept_lines = [line for line in a_lines if line.rstrip("\n") not in b_lines]
    tmp_path = file_a.with_suffix(file_a.suffix + ".tmp")
    tmp_path.write_text("".join(kept_lines), encoding="utf-8")
    tmp_path.replace(file_a)


if __name__ == "__main__":
    raise SystemExit(main())
