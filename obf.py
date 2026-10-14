#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line obfuscation tool for Python source files. It should take the path of a Python file as its single input argument, read that file's contents, and output a shell-script version of the code to standard output.
The generated output must be a shell script (not Python) that reconstructs the original source and executes it when run. Specifically, the tool should:
- Split the source text into small fixed-size chunks.
- Assign each chunk to a short, generated shell variable name, using a naming sequence that starts with single ASCII letters, then letter-plus-"z" combinations, then two-letter-plus-"z" combinations, so that names remain unique and compact.
- Emit one assignment per chunk, escaping single quotes within each chunk so the shell treats every value literally.
- Finish with a single evaluation line that concatenates all the variable references in order, so the shell reassembles and runs the original code.
Ensure the output is valid, self-contained shell syntax, that the naming scheme never produces collisions, and that the tool handles arbitrary source text, including empty files, files whose length is not a multiple of the chunk size, and content containing quotes or special characters. The tool should be runnable directly from the command line and print its result without any extra commentary.
---"""

from __future__ import annotations
import string
import sys


def varnames():
    letters = string.ascii_letters
    for c in letters:
        yield c
    for c in letters:
        yield c + "z"
    for c in letters:
        for d in letters:
            yield c + d + "z"


def obfuscate(src: str) -> str:
    names = varnames()
    out = []
    eval_parts = []
    CHUNK = 3
    for i in range(0, len(src), CHUNK):
        piece = src[i : i + CHUNK]
        name = next(names)
        escaped = piece.replace("'", "'\\''")
        out.append(f"{name}='{escaped}';")
        eval_parts.append(f"${name}")
    out.append('eval "' + "".join(eval_parts) + '"')
    return "\n".join(out)


if __name__ == "__main__":
    src = open(sys.argv[1]).read()
    print(obfuscate(src))
