#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python utility script that discovers project Python files (via a helper module "dh" providing get_pyfiles and mpf) and processes each one to strip comments and docstrings using the tokenize module, then collapses the remaining code into non-empty, stripped lines.
Include a helper function that shortens identifier names by removing vowels (leaving names starting with underscore untouched), intended for lightweight code minification or obfuscation analysis.
The script should read each target file's source as UTF-8, apply the comment/docstring removal, and prepare the cleaned lines for further processing such as writing output or import handling."""

import io
import re
import sys
import tokenize
from pathlib import Path
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
        if toktype == tokenize.COMMENT or (
            toktype == tokenize.STRING and prev_toktype == tokenize.INDENT
        ):
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

    content_no_multiline_strings = re.sub(
        "'''.*?'''|\\\"\\\"\\\".*?\\\"\\\"\\\"", "", content, flags=re.DOTALL
    )
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
