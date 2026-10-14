#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a shell-style configuration or build-definition file, resolves simple variable assignments and their references, and then extracts and evaluates a single embedded command expression to produce a final, fully expanded result.
The tool should accept a file path as its main input (via command-line arguments) and print or return the resolved output to the user. Its key behaviors are:
- Parse plain variable assignments from the file, supporting both single-quoted values (taken literally) and double-quoted values (where common escape sequences are honored).
- Locate the first occurrence of an `eval` directive whose argument is a double-quoted string, and extract that expression.
- Substitute references of the form `${NAME}` (and any equivalent simple forms) in the extracted expression using the parsed variables, leaving unknown references unchanged rather than failing.
- Produce the fully substituted expression as the result, and report clearly when no `eval` directive is found or when the input file cannot be read.
- Handle errors gracefully with informative messages and non-zero exit codes for invalid usage or missing files.
- Keep the implementation self-contained, readable, and dependency-free beyond the Python standard library, with a clear command-line interface that includes help text.
---"""

from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

_ASSIGN_RE = re.compile(
    r"""
    (?P<name>[A-Za-z_][A-Za-z0-9_]*)=
    (?:
        '(?P<single>[^']*)'             # single-quoted value
      | "(?P<double>(?:[^"\\]|\\.)*)"   # double-quoted value (with escapes)
    )
    """,
    re.VERBOSE | re.DOTALL,
)


def parse_assignments(src: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in _ASSIGN_RE.finditer(src):
        name = m.group("name")
        if m.group("single") is not None:
            out[name] = m.group("single")
        else:
            out[name] = re.sub(r"\\([\"\\$`])", r"\1", m.group("double"))
    return out


_EVAL_RE = re.compile(r'\beval\s+"((?:[^"\\]|\\.)*)"')


def find_eval_expr(src: str) -> str | None:
    m = _EVAL_RE.search(src)
    return m.group(1) if m else None


def substitute(expr: str, variables: dict[str, str]) -> str:
    def repl(m: re.Match) -> str:
        name = m.group(1) or m.group(2)
        return variables.get(name, m.group(0))

    expr = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, expr)
    expr = re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", repl, expr)
    return expr


def pretty(code: str) -> str:
    code = code.replace(";clear;", ";\nclear;")
    code = code.replace(";\n}", ";\n}\n")
    return code


def pick_output(inp: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    suffix = inp.suffix or ".sh"
    candidate = inp.with_name(f"{inp.stem}.deobf{suffix}")
    if candidate == inp:
        candidate = inp.with_name(f"{inp.name}.deobf.sh")
    base = candidate
    n = 1
    while candidate.exists():
        candidate = base.with_name(f"{base.stem}.{n}{base.suffix}")
        n += 1
    return candidate


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("input", help="obfuscated bash file")
    ap.add_argument("-o", "--output", help="output path (optional)")
    args = ap.parse_args()
    inp = Path(args.input)
    if not inp.is_file():
        print(f"error: {inp}: not a file", file=sys.stderr)
        return 1
    src = inp.read_text(encoding="utf-8", errors="replace")
    variables = parse_assignments(src)
    expr = find_eval_expr(src)
    if expr is None:
        print('error: no eval "…" expression found', file=sys.stderr)
        return 1
    resolved = substitute(expr, variables)
    resolved = pretty(resolved)
    out = pick_output(inp, args.output)
    out.write_text(resolved.rstrip() + "\n", encoding="utf-8")
    print(f"[+] wrote {out}  ({len(resolved.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
