#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations

import argparse
import ast
import json
import re
import textwrap
from pathlib import Path

OUTPUT_DIR = Path.home() / "isaac" / "may" / "q1" / "prompts"
MAX_LINE = 80
LIVEDOC_RE = re.compile(r"^LiveDoc:\s*https?://\S+\s*$")


def strip_quotes(doc: str) -> str:
    """Strip leading/trailing triple or single quotes from a docstring."""
    doc = doc.strip()
    for quote in ('"""', "'''", '"', "'"):
        if doc.startswith(quote) and doc.endswith(quote) and len(doc) > 2 * len(quote):
            doc = doc[len(quote) : -len(quote)]
            break
    return doc.strip()


def extract_module_docstring(path: Path) -> str | None:
    """Parse the given Python file and return its module-level docstring, if any."""
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    doc = ast.get_docstring(tree, clean=False)
    if not doc:
        return None
    return strip_quotes(doc)


def strip_trailing_livedoc(doc: str) -> str:
    """Drop a trailing '---' + 'LiveDoc: <url>' block if present."""
    lines = doc.rstrip().splitlines()
    if len(lines) >= 2 and lines[-2].strip() == "---" and LIVEDOC_RE.match(lines[-1].strip()):
        lines = lines[:-2]
    return "\n".join(lines).rstrip()


def split_sentences(text: str) -> list[str]:
    """Naive sentence splitter: break after . ! ? followed by whitespace + capital."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def format_docstring(doc: str, width: int = MAX_LINE) -> str:
    """One sentence per line, wrapped to `width` on word boundaries."""
    lines: list[str] = []
    for sentence in split_sentences(doc):
        wrapped = textwrap.wrap(
            sentence,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        ) or [""]
        lines.extend(wrapped)
    return "\n".join(lines)


def remove_module_docstring(path: Path) -> bool:
    """Remove the module-level docstring from `path` in place. Returns True on success."""
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    if not tree.body:
        return False
    first = tree.body[0]
    if not (
        isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str)
    ):
        return False

    lines = source.splitlines(keepends=True)
    start = first.lineno - 1
    end = first.end_lineno  # exclusive slice endpoint
    new_source = "".join(lines[:start] + lines[end:])

    # A module that contained only the docstring must remain valid Python.
    if not new_source.strip():
        new_source = "pass\n"

    path.write_text(new_source, encoding="utf-8")
    return True


def process(root: Path, out_dir: Path, fmt: str, remove: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for py_file in sorted(root.rglob("*.py")):
        doc = extract_module_docstring(py_file)
        if doc:
            doc = strip_trailing_livedoc(doc)
        if doc:
            formatted = format_docstring(doc)
            stem = py_file.stem
            if fmt == "json":
                out_path = out_dir / f"{stem}.json"
                payload = {py_file.name: formatted}
                out_path.write_text(
                    json.dumps(payload, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            else:
                out_path = out_dir / f"{stem}.txt"
                out_path.write_text(formatted + "\n", encoding="utf-8")
            print(f"[+] {py_file} -> {out_path}")

        if remove and remove_module_docstring(py_file):
            print(f"[-] removed module docstring from {py_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove the module docstring from each source .py file in place.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Directory to scan recursively (default: cwd).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR}).",
    )
    args = parser.parse_args()
    process(args.root.resolve(), args.out_dir, args.format, args.remove)


if __name__ == "__main__":
    main()
