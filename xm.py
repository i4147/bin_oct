#!/data/data/com.termux/files/usr/bin/python
"""Extract module docstrings from Python files and save them as .txt or .json."""

from __future__ import annotations

import argparse
import ast
import json
import re
import textwrap
from pathlib import Path

OUTPUT_DIR = Path.home() / "isaac" / "may" / "q1" / "prompts"
MAX_LINE = 80


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


def process(root: Path, out_dir: Path, fmt: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for py_file in sorted(root.rglob("*.py")):
        doc = extract_module_docstring(py_file)
        if not doc:
            continue
        formatted = format_docstring(doc)
        stem = py_file.stem
        if fmt == "json":
            out_path = out_dir / f"{stem}.json"
            payload = {py_file.name: formatted}
            out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            out_path = out_dir / f"{stem}.txt"
            out_path.write_text(formatted + "\n", encoding="utf-8")
        print(f"[+] {py_file} -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
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
    process(args.root.resolve(), args.out_dir, args.format)


if __name__ == "__main__":
    main()
