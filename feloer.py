#!/data/data/com.termux/files/usr/bin/python3.12
"""Prepend an AI-generated "how to reproduce this" prompt as a module docstring to one or more self-contained .py files."""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import time

from dh import DOC_TH1, DOC_TH2

FELO_SUPERAGENT = "/data/data/com.termux/files/home/bashbin/felo-sa.mjs"
FELO_TIMEOUT = int(os.environ.get("FELO_TIMEOUT", "300"))

PROMPT_TEMPLATE = """\
Provide a prompt for ai agent that can produce the following Python code.
The prompt must describe the script's purpose, its main inputs/outputs, and any notable behavior.

Strict output rules:
- Output ONLY the prompt text.
- Do not include the code itself.
- Do not repeat these instructions.
- Do not add a preamble like "Sure" or "Here is".
Answer in ENGLISH ONLY.

Code:
{code}
"""

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
FENCE_RE = re.compile(r"^\s*```.*$", re.MULTILINE)
SHELL_PROMPT_RE = re.compile(r"^\s*(?:\$|>|>>>)\s.*$", re.MULTILINE)
ECHO_LINE_RE = re.compile(
    r"^\s*(?:felo|feli|SuperAgent|Received)[>:\s].*$",
    re.MULTILINE | re.IGNORECASE,
)
PREAMBLE_RE = re.compile(
    r"^(?:sure[,!.]?|certainly[,!.]?|here(?:'s| is)[^\n]*|of course[,!.]?)\s*\n",
    re.IGNORECASE,
)


def clean_response(text: str) -> str:
    text = ANSI_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    m = re.search(r"^\s*Received\s*:", text, re.MULTILINE | re.IGNORECASE)
    if m:
        after = text[m.end() :]
        after = after.split("\n", 1)[1] if "\n" in after else ""
        after = re.sub(r"^\s*\n+", "", after)
        text = after

    text = re.sub(
        r"^\s*(?:SuperAgent|felo|feli)\b.*$",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    text = FENCE_RE.sub("", text)
    text = SHELL_PROMPT_RE.sub("", text)
    text = PREAMBLE_RE.sub("", text)
    text = text.strip()

    if not text:
        return ""

    if "\n" not in text:
        parts = re.split(r"(?<=[.!?])\s+", text)
        text = "\n".join(p.strip() for p in parts if p.strip())

    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def make_docstring(text: str) -> str:

    safe = re.sub(r"\\", r"\\\\", text)

    safe = re.sub(r'"""', r'\\"\\"\\"', safe)

    #    safe = text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')

    return DOC_TH1 + safe + DOC_TH1 + "\n\n"


def split_header(body: str) -> tuple[str, str]:
    lines = body.split("\n")
    idx = 0
    if lines and lines[0].startswith("#!"):
        idx = 1
    if idx < len(lines) and re.match(r"^#.*coding[:=]", lines[idx]):
        idx += 1
    if idx == 0:
        return "", body
    return "\n".join(lines[:idx]) + "\n", "\n".join(lines[idx:])


def has_module_docstring(body: str) -> bool:
    s = body.lstrip()
    return s.startswith((DOC_TH1, DOC_TH2))


def ask_felo(code: str) -> str:
    prompt = PROMPT_TEMPLATE.format(code=code)

    cmd = [
        "node",
        FELO_SUPERAGENT,
        "--query",
        prompt,
        "--accept-language",
        "en",
        "--timeout",
        "300",
        "--verbose",
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=FELO_TIMEOUT,
    )
    if proc.returncode != 0:
        msg = f"felo exited {proc.returncode}: {proc.stderr.strip()[:300]}"
        raise RuntimeError(msg)
    return proc.stdout


def annotate(path: str, dry_run: bool) -> None:
    if path.endswith(("__init__.py", "__main__.py", "setup.py", "main.py", "test.py", "conf.py", "tests.py")):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    header, body = split_header(content)

    if has_module_docstring(body):
        print(f"[skip] {path}: module docstring already present")
        return

    print(f"[ask ] {path}")
    try:
        raw = ask_felo(content)
    except FileNotFoundError:
        sys.exit(f"ERROR: '{FELO_CMD}' CLI not found in PATH.")
    except subprocess.TimeoutExpired:
        print(f"[time] {path}: felo timed out after {FELO_TIMEOUT}s")
        return
    except RuntimeError as e:
        print(f"[err ] {path}: {e}")
        return

    if os.environ.get("FELO_DEBUG"):
        print("----- RAW RESPONSE -----")
        print(raw)
        print("----- END RAW ----------")

    cleaned = clean_response(raw)
    if not cleaned:
        print(f"[none] {path}: empty response after cleaning")
        return

    docstring = make_docstring(cleaned)
    new_content = header + docstring + body

    if dry_run:
        print(f"--- would prepend to {path} ---")
        print(docstring, end="")
        print("--- end ---\n")
        return

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[ok  ] {path}")


def collect_files(inputs: list[str], pattern: str) -> list[str]:
    """Expand files/dirs into a de-duplicated, sorted list of matching files.

    - Regular files are taken as-is (no pattern filtering).
    - Directories are walked recursively; only names matching ``pattern``
      are included.
    - The running script itself is excluded.
    """
    me = os.path.abspath(__file__)
    seen: set[str] = set()
    out: list[str] = []

    def add(path: str) -> None:
        ap = os.path.abspath(path)
        if ap == me:
            return
        if ap in seen:
            return
        seen.add(ap)
        out.append(path)

    for inp in inputs:
        if os.path.isfile(inp):
            add(inp)
        elif os.path.isdir(inp):
            for root, _dirs, names in os.walk(inp):
                for name in names:
                    if fnmatch.fnmatch(name, pattern):
                        add(os.path.join(root, name))
        else:
            print(f"[warn] skipping (not a file or directory): {inp}")

    return sorted(out)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "paths",
        nargs="*",
        help="One or more files or directories. If omitted, the current directory is processed recursively.",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--pattern",
        default="*.py",
        help="Glob pattern used when expanding directories (default: *.py).",
    )
    ap.add_argument("--delay", type=float, default=0.0)
    args = ap.parse_args()

    inputs = args.paths or ["."]
    paths = collect_files(inputs, args.pattern)

    if not paths:
        print(f"No matching files found (pattern={args.pattern!r}).")
        return

    print(f"Found {len(paths)} file(s). dry_run={args.dry_run}")
    for i, p in enumerate(paths, 1):
        print(f"\n=== [{i}/{len(paths)}] {p} ===")
        annotate(p, args.dry_run)
        if args.delay and i < len(paths):
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
