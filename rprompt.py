#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a source file or a directory of Python files as input, strips out all comments and docstrings from the Python code, and writes the cleaned code back out as a minified or compacted version. The script should process every Python file it finds in the given location, handle nested folders when appropriate, and preserve the original code's functional behavior while removing human-readable documentation. It should also include a utility for renaming identifiers to shorter names, so that the resulting code is more compact, while keeping names that must not change (such as dunder names, keywords, and built-ins) intact. The script should accept command-line arguments to specify the target path and where the output should be saved, and it should report clearly which files were processed and any errors encountered without stopping the entire run on a single failure. Output should be written to a separate location so the original files are never overwritten unless explicitly requested.
---"""

from __future__ import annotations
import io
from pathlib import Path
import re
import sys
import tokenize
from dh import get_pyfiles, mpf


def remove_comments_and_docstrings(source_code: str) -> str:
    io_obj = io.StringIO(source_code)
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    for tok in tokenize.generate_tokens(io_obj.readline):
        toktype = tok[0]
        tok_string = tok[1]
        start_lineno, start_col = tok[2]
        _end_lineno, end_col = tok[3]
        if start_lineno > last_lineno:
            last_col = 0
        if toktype == tokenize.COMMENT or (toktype == tokenize.STRING and prev_toktype == tokenize.INDENT):
            pass
        else:
            if start_col > last_col:
                out += " " * (start_col - last_col)
            out += tok_string
            prev_toktype = toktype
            last_col = end_col
            last_lineno = start_lineno
    return out


def shorten_variable_name(name):
    if not name or name.startswith("_"):
        return name
    vowels = "aeiouAEIOU"
    return "".join([char for char in name if char not in vowels])


def process_file(path) -> None:
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    content_no_comments = remove_comments_and_docstrings(content)
    lines = content_no_comments.splitlines()
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    "\n".join(non_empty_lines)
    import keyword

    keywords = set(keyword.kwlist)

    def replacer(match):
        name = match.group(0)
        if name in keywords:
            return name
        return shorten_variable_name(name)

    content_no_multiline_strings = re.sub("'''.*?'''|\\\"\\\"\\\".*?\\\"\\\"\\\"", "", content, flags=re.DOTALL)
    content_no_comments_single = re.sub("#.*", "", content_no_multiline_strings)
    lines = content_no_comments_single.splitlines()
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    final_content = "\n".join(non_empty_lines)
    compressed_path = path.with_stem(path.stem + "_compressed")
    compressed_path.write_text(final_content, encoding="utf-8")


if __name__ == "__main__":
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = []
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(get_pyfiles(p))
    else:
        files = get_pyfiles(cwd)
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)
