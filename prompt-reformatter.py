#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations
import ast
from pathlib import Path
import re
import sys


SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "lazy",
}

# --- Split rules ----------------------------------------------------------- #

# Whitespace immediately preceding a list marker or a **Title**.
# Recognised markers: "1."  "2)"  "(3)"  "-"  "*"  "•"  "**Some Title**"
_BEFORE_MARKER = re.compile(r"[ \t\r\n]+(?=(?:\d+[.)]|\(\d+\)|[-*\u2022]|\*\*[^*\n]+\*\*)\s)")

# Comma followed by space/tab.  Applied unconditionally.
_COMMA_SPLIT = re.compile(r",[ \t]+")

# Semicolon followed by space/tab.  Applied only on lines > MAX_LINE.
_SEMICOLON_SPLIT = re.compile(r";[ \t]+")

# Threshold for the fallback "; " split.
MAX_LINE = 80

# Captures the optional string prefix (r/u/b/f ...) and the opening quote.
_STRING_HEAD = re.compile(r'^([rRbBuUfF]*)("""|\'\'\'|"|\')')  # extra """


def reformat(text: str) -> str:
    """Insert newlines before list markers, after commas, and (on long
    lines) after semicolons.  Leading/trailing whitespace is preserved.
    """
    if not text.strip():
        return text

    lead_match = re.match(r"^([ \t]*(?:\r?\n[ \t]*)*)", text)
    leading = lead_match.group(1) if lead_match else ""

    trail_match = re.search(r"([ \t]*(?:\r?\n[ \t]*)*)$", text)
    trailing = trail_match.group(1) if trail_match else ""

    # Indentation used for the newly-created lines.
    indent = leading.rsplit("\n", 1)[-1] if "\n" in leading else ""

    core_end = len(text) - len(trailing) if trailing else len(text)
    core = text[len(leading) : core_end]

    # 1) Break before list markers / **Titles**.
    core = _BEFORE_MARKER.sub("\n" + indent, core)

    # 2) Break at every ", " (comma stays at the end of the previous line).
    core = _COMMA_SPLIT.sub(",\n" + indent, core)

    # 3) Fallback: on any line still longer than MAX_LINE, break at "; ".
    #    (Swap blocks 2 and 3 if you'd rather honour semicolons first.)
    if MAX_LINE > 0:
        rebuilt = []
        for line in core.split("\n"):
            if len(line) > MAX_LINE and ";" in line:
                line = _SEMICOLON_SPLIT.sub(";\n" + indent, line)
            rebuilt.append(line)
        core = "\n".join(rebuilt)

    return leading + core + trailing


def process_file(path: Path) -> bool:
    try:
        source = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    code = reformat(source)
    path.write_text(code, encoding="utf-8")
    return True


# --------------------------------------------------------------------------- #
# Entry point                                                                 #
# --------------------------------------------------------------------------- #
def iter_files(root: Path):
    for path in sorted(root.rglob("*.txt")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.is_file():
            yield path


def main(root: Path | None = None) -> int:
    root = (root or Path.cwd()).resolve()
    changed = 0
    for path in iter_files(root):
        if process_file(path):
            print(f"formatted: {path.name}")
            changed += 1
    print(f"{changed} file(s) updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
