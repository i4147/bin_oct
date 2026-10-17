#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations
import ast
from pathlib import Path
import re
import sys


# Directories we never descend into.
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    "build",
    "dist",
    ".eggs",
    "site-packages",
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
_STRING_HEAD = re.compile(r'^([rRbBuUfF]*)("""|\'\'\'|"|\')')


# --------------------------------------------------------------------------- #
# Docstring reformatting                                                      #
# --------------------------------------------------------------------------- #
def reformat_docstring_body(text: str) -> str:
    """Insert newlines before list markers, after commas, and (on long
    lines) after semicolons.  Leading/trailing whitespace is preserved.
    """
    if not text.strip():
        return text

    # Preserve leading / trailing whitespace so indentation keeps working.
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


# --------------------------------------------------------------------------- #
# AST helpers                                                                 #
# --------------------------------------------------------------------------- #
def _module_docstring_node(tree: ast.Module) -> ast.Constant | None:
    if not tree.body:
        return None
    first = tree.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        return first.value
    return None


def _offset(lines: list[str], lineno: int, col: int) -> int:
    return sum(len(line) for line in lines[: lineno - 1]) + col


# --------------------------------------------------------------------------- #
# Per-file processing                                                         #
# --------------------------------------------------------------------------- #
def process_file(path: Path) -> bool:
    """Return True if *path* was modified."""
    try:
        source = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    node = _module_docstring_node(tree)
    if node is None:
        return False

    # Extract the raw text of the docstring node from the source.
    lines = source.splitlines(keepends=True)
    start = _offset(lines, node.lineno, node.col_offset)
    end = _offset(lines, node.end_lineno, node.end_col_offset)
    raw = source[start:end]

    head = _STRING_HEAD.match(raw)
    if not head or not raw.endswith(head.group(2)):
        return False
    prefix, quote = head.group(1), head.group(2)

    inner = raw[len(prefix) + len(quote) : -len(quote)]
    new_inner = reformat_docstring_body(inner)
    if new_inner == inner:
        return False

    if len(quote) == 1:
        # A single-quoted string cannot contain a real newline; promote to
        # triple quotes if the content makes that safe.
        if '"""' in new_inner or new_inner.endswith('"'):
            return False
        new_raw = f'{prefix}"""{new_inner}"""'
    else:
        new_raw = prefix + quote + new_inner + quote

    path.write_bytes((source[:start] + new_raw + source[end:]).encode("utf-8"))
    return True


# --------------------------------------------------------------------------- #
# Entry point                                                                 #
# --------------------------------------------------------------------------- #
def iter_python_files(root: Path):
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.is_file():
            yield path


def main(root: Path | None = None) -> int:
    root = (root or Path.cwd()).resolve()
    changed = 0
    for path in iter_python_files(root):
        if process_file(path):
            print(f"formatted: {path.relative_to(root)}")
            changed += 1
    print(f"{changed} file(s) updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
