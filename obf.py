#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script that obfuscates another Python source file into a shell script. Requirements:

**Purpose:** Read a Python source file and emit a shell script (to stdout) that reconstructs and executes that source via `eval`, hiding its contents from casual inspection.

**Shebang and imports:** Begin with a Termux-style Python shebang (`#!/data/data/com.termux/files/usr/bin/env python`). Include `from __future__ import annotations`. Import only `string` and `sys` from the standard library.

**Variable name generator:** Implement a generator function `varnames()` that yields shell-safe identifiers in three tiers, using `string.ascii_letters`:
1. Each single letter (52 names).
2. Each letter followed by `z` (e.g., `az`, `bz`, ...).
3. Every two-letter combination of letters, with `z` appended (e.g., `aaz`, `abz`, ...).

**Obfuscation function `obfuscate(src: str) -> str`:**
- Initialize a name generator and empty lists for output lines and eval references.
- Split the source string into consecutive chunks of exactly 3 characters (the final chunk may be shorter).
- For each chunk, take the next generated name, escape every single quote by replacing `'` with `'\\''` (standard POSIX shell single-quote escaping), and append a line of the form `NAME='escaped_chunk';`.
- Record a `$NAME` reference for each chunk.
- After all assignment lines, append one final line: `eval "` followed by all references concatenated with no separator, then a closing double quote.
- Return all lines joined with newlines (no trailing newline added beyond the join).

**Main block (`if __name__ == "__main__":`):**
- Read the file path from `sys.argv[1]` and load its full contents as text using the default `open()` behavior (no explicit encoding or context manager required, but a context manager is acceptable).
- Print the result of `obfuscate` to stdout using `print`.
- No argument validation or error handling is required; a missing argument or unreadable file will raise the default Python exception.

**Behavior and edge cases to preserve:**
- Output is a POSIX shell script; the chunking and quoting must produce output that reconstructs the source exactly when run through the shell.
- Empty input produces only the `eval ""` line.
- The name generator is limited to roughly 52 + 52 + 2704 names; inputs requiring more chunks than that will exhaust the generator and raise `StopIteration` via `next()`.
- Names are alphanumeric, so they are safe unquoted shell variable references.

**Usage:** `python <script> <input_file.py> > output.sh`, then run the output with `sh output.sh` to execute the original program.

Write the code in clean, idiomatic Python 3 with type hints on the `obfuscate` signature and brief comments matching the style of a small utility script.
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
