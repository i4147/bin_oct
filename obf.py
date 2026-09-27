#!/data/data/com.termux/files/home/.local/bin/python
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
