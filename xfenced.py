#!/data/data/com.termux/files/usr/bin/python
"""
extract_py.py

Scan Markdown files for fenced Python code blocks (```python ... ```) and
write each block to its own file in the current directory:

    ex01.py, ex02.py, ex03.py, ...

Usage:
    python extract_py.py                # process every *.md in the current dir
    python extract_py.py notes.md       # process specific file(s)
    python extract_py.py *.md           # shell expansion also works
"""

from __future__ import annotations
from pathlib import Path
import re
import sys


# --------------------------------------------------------------------------- #
# Regex for fenced Python code blocks.
#
#   ^```(?:python|py)\b  ->  opening fence tagged "python" or "py"
#   \s*\n                ->  rest of the opening line (e.g. trailing spaces)
#   (.*?)                ->  the code body (non-greedy, captured)
#   ^```[ \t]*$          ->  closing fence on its own line
#
# Flags:
#   re.DOTALL     -> "." also matches newlines (needed for the body)
#   re.MULTILINE  -> "^" / "$" match at the start/end of every line
# --------------------------------------------------------------------------- #
CODE_BLOCK_RE = re.compile(
    r"^```(?:python|py)\b\s*\n(.*?)^```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)


def extract_blocks(text: str) -> list[str]:
    """Return every Python code block found in `text` as a list of strings."""
    return [match.group(1) for match in CODE_BLOCK_RE.finditer(text)]


def markdown_files(argv: list[str]) -> list[Path]:
    """
    Decide which Markdown files to scan.

    - If command-line arguments are given, treat them as file paths.
    - Otherwise, use every *.md file in the current working directory.
    """
    if len(argv) > 1:
        return [Path(arg) for arg in argv[1:]]
    return sorted(Path.cwd().glob("*.md"))


def main() -> None:
    out_dir = Path.cwd()  # write outputs next to where we're run
    counter = 0  # global counter across all markdown files

    for md_path in markdown_files(sys.argv):
        if not md_path.is_file():
            print(f"skip (not a file): {md_path}")
            continue

        # Read the markdown source (assume UTF-8; tweak if you need otherwise)
        text = md_path.read_text(encoding="utf-8")

        for code in extract_blocks(text):
            counter += 1
            out_path = out_dir / f"ex{counter:02d}.py"
            out_path.write_text(code, encoding="utf-8")
            print(f"{md_path.name}  ->  {out_path.name}")

    print(f"\nDone. Extracted {counter} Python code block(s).")


if __name__ == "__main__":
    main()
