#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line utility script (targeted to run under Termux's Python 3.12 interpreter, using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that scans Python source files and reformats their module-level docstrings.

The script's purpose:
- For a given Python file (or set of files), locate the module-level docstring, which must be the very first statement in the file (an `ast.Expr` node wrapping a string `ast.Constant`).
- Reformat the docstring's text content: strip leading/trailing whitespace, collapse all internal whitespace/newlines into single spaces, then split the text into sentences (using a regex that splits after `.`, `!`, or `?` followed by whitespace) and join those sentences with newline characters, so each sentence ends up on its own line.
- Rebuild the docstring using triple quotes, preserving the original quote style (`'''` or `\"\"\"`) detected from the source segment, defaulting to `\"\"\"` if undetermined. If the reformatted content itself contains the chosen triple-quote sequence, switch to the other quote style, and if that still conflicts, escape the quote characters appropriately so the resulting docstring remains syntactically valid.
- Replace the original docstring text in the source file with the newly formatted docstring, preserving the rest of the file's content unchanged, by calculating the exact start and end character offsets of the original docstring node within the source (using `node.lineno`/`node.col_offset` and summing line lengths) and splicing in the new docstring text.

Main inputs/outputs:
- Input: path(s) to Python source file(s), passed as function arguments (e.g., via a `Path` object), to be read using `tokenize.open` so the file's declared encoding is respected.
- Output: the function returns a boolean indicating whether the file was successfully processed and modified (e.g., `False` if the file can't be read, can't be parsed due to a `SyntaxError`, has an empty body, the first statement isn't a plain string expression docstring, the source segment can't be extracted, or the literal can't be evaluated via `ast.literal_eval`).
- The script should use the `ast` module to parse and locate the docstring node, `re` for whitespace normalization and sentence splitting, `tokenize` for encoding-aware file reading, and `pathlib.Path` for file path handling.

Notable behavior and edge cases to handle:
- Gracefully return `False` (without raising) on file read errors, syntax errors, missing/empty docstrings, or failures extracting/evaluating the docstring's source segment via `ast.get_source_segment` and `ast.literal_eval`.
- Correctly detect whether the original docstring used single (`'''`) or double (`\"\"\"`) triple quotes, and preserve that style when rewriting, only switching or escaping when there's a quote-character conflict with the reformatted content.
- Accurately compute the byte/character offset range of the original docstring in the full source text (accounting for multi-line content before the docstring) so that only the docstring portion is replaced, leaving all other code, comments, and formatting in the file untouched.
- Should work as an idempotent formatting tool runnable on one or more files to normalize module docstrings into a one-sentence-per-line style.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/3CtR2oNsstfSbjF9gfp9rw"""

from __future__ import annotations
import ast
import re
import tokenize
from pathlib import Path


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
