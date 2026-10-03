#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that obfuscates a shell script by splitting its source code into small chunks (3 characters each) and assigning each chunk to a uniquely generated variable name, produced via a generator that yields single letters, then letter+"z" combinations, then two-letter+"z" combinations.
The script should read the input shell script's path from the first command-line argument, generate shell variable assignment statements for each chunk (properly escaping single quotes), and finally output an `eval` statement that concatenates all the variable references to reconstruct and execute the original script.
The obfuscated result is printed to stdout."""

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
