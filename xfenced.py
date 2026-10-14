#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that extracts Python code blocks from Markdown files and saves each one as a separate standalone Python file.
The tool should accept zero or more Markdown file paths as command-line arguments. If no paths are given, it should automatically process all Markdown files in the current working directory, in a consistent sorted order. For each path, it should skip anything that is not a regular file and report that it was skipped.
For every file processed, the tool should locate all fenced code blocks explicitly tagged as Python (using common tags such as "python" or "py"), ignoring blocks in other languages. Each matched block's content should be captured exactly as written, preserving indentation and line breaks.
Each extracted block should be written to the current working directory as its own file, named with a zero-padded sequential number (for example, ex01.py, ex02.py, and so on), numbered globally across all processed Markdown files in the order encountered. The files should be saved using UTF-8 encoding.
As progress output, the tool should print one line per extracted block showing the source Markdown filename and the newly created output filename. After processing everything, it should print a closing summary stating the total number of Python code blocks extracted.
The script should be runnable directly from the command line and should not require any external dependencies beyond the Python standard library.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys

CODE_BLOCK_RE = re.compile(
    r"^```(?:python|py)\b\s*\n(.*?)^```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)


def extract_blocks(text: str) -> list[str]:
    return [match.group(1) for match in CODE_BLOCK_RE.finditer(text)]


def markdown_files(argv: list[str]) -> list[Path]:
    if len(argv) > 1:
        return [Path(arg) for arg in argv[1:]]
    return sorted(Path.cwd().glob("*.md"))


def main() -> None:
    out_dir = Path.cwd()
    counter = 0
    for md_path in markdown_files(sys.argv):
        if not md_path.is_file():
            print(f"skip (not a file): {md_path}")
            continue
        text = md_path.read_text(encoding="utf-8")
        for code in extract_blocks(text):
            counter += 1
            out_path = out_dir / f"ex{counter:02d}.py"
            out_path.write_text(code, encoding="utf-8")
            print(f"{md_path.name}  ->  {out_path.name}")
    print(f"\nDone. Extracted {counter} Python code block(s).")


if __name__ == "__main__":
    main()
