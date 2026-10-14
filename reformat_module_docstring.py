#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory of Python source files and reformats the module-level docstring of each file so that it is consistently laid out, one sentence per line. The tool should accept a directory path (or a single file) as input, recursively locate `.py` files, and for each file that has a valid module docstring at the top, rewrite only that docstring: collapse irregular whitespace, split the text into sentences, and place each sentence on its own line, while preserving the original triple-quote style and leaving the rest of the file untouched. Files that cannot be read, that contain syntax errors, that have no module docstring, or where the docstring cannot be located precisely should be skipped without crashing, and the script should report a summary at the end listing how many files were processed, modified, and skipped. The tool should write changes back to disk in place, produce output that remains valid Python, and handle common text encodings gracefully. Include a dry-run option that shows which files would change without modifying them, and provide clear command-line usage with helpful error messages for invalid paths.
---"""

from __future__ import annotations
import ast
from pathlib import Path
import re
import tokenize


def reformat_docstring(content):
    content = content.strip()
    content = re.sub(r"\s+", " ", content)
    sentences = re.split(r"(?<=[.!?])\s+", content)
    return "\n".join(sentences)


def process_file(path):
    try:
        with tokenize.open(path) as f:
            source = f.read()
    except Exception:
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
    node = first.value
    segment = ast.get_source_segment(source, node)
    if segment is None:
        return False
    if segment.startswith("'''"):
        quote = "'''"
    elif segment.startswith('"""'):
        quote = '"""'
    else:
        quote = '"""'
    try:
        value = ast.literal_eval(segment)
    except Exception:
        return False
    new_content = reformat_docstring(value)
    if quote in new_content:
        if quote == '"""':
            quote = "'''"
        else:
            quote = '"""'
        if quote in new_content:
            new_content = new_content.replace(quote, "\\" + quote[0] * 3)
    new_docstring = quote + new_content + quote
    lines = source.splitlines(keepends=True)
    start = sum(len(lines[i]) for i in range(node.lineno - 1)) + node.col_offset
    end = sum(len(lines[i]) for i in range(node.end_lineno - 1)) + node.end_col_offset
    new_source = source[:start] + new_docstring + source[end:]
    if new_source == source:
        return False
    try:
        ast.parse(new_source)
    except SyntaxError:
        return False
    try:
        path.write_text(new_source, encoding="utf-8")
    except Exception:
        return False
    return True


def main():
    for path in Path().rglob("*.py"):
        if path.is_file() and process_file(path):
            try:
                rel = path.relative_to(Path.cwd())
            except ValueError:
                rel = path
            print(rel)


if __name__ == "__main__":
    main()
