#!/data/data/com.termux/files/home/.local/bin/python
"""
annotate_felo.py

Prepend an AI-generated "how to reproduce this" prompt as a module
docstring to every self-contained .py file in the current directory.

Uses the felo CLI:
    felo superagent --query "..." --accept-language en --timeout 300 --json --verbose

Usage:
    python annotate_felo.py --dry-run
    python annotate_felo.py
    python annotate_felo.py --recursive --delay 2
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys
import time

FELO_CMD = os.environ.get("FELO_CMD", "felo")
FELO_SUBCMD = os.environ.get("FELO_SUBCMD", "superagent")
FELO_TIMEOUT = int(os.environ.get("FELO_TIMEOUT", "300"))

PROMPT_TEMPLATE = """\
Answer in ENGLISH ONLY. Never reply in Japanese.

Provide a brief prompt that can produce the following Python code.
The prompt must be plain prose (2-5 sentences). It must describe the
script's purpose, its main inputs/outputs, and any notable behavior.

Strict output rules:
- Output ONLY the prompt text.
- No markdown, no code fences, no bullet lists, no headings.
- No shell transcript, no "$" prompts, no commentary.
- Do not include the code itself.
- Do not repeat these instructions.
- Do not add a preamble like "Sure" or "Here is".

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
    safe = text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    return '"""' + safe + '"""\n\n'


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
    return s.startswith('"""') or s.startswith("'''")


def ask_felo(code: str) -> str:
    prompt = PROMPT_TEMPLATE.format(code=code)

    cmd = [
        FELO_CMD,
        FELO_SUBCMD,
        "--query",
        prompt,
        "--accept-language",
        "en",
        "--timeout",
        "300",
        "--json",
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
        raise RuntimeError(
            f"felo exited {proc.returncode}: {proc.stderr.strip()[:300]}"
        )
    return proc.stdout


def annotate(path: str, dry_run: bool) -> None:
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


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pattern", default="*.py")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--delay", type=float, default=0.0)
    args = ap.parse_args()

    if args.recursive:
        paths = glob.glob(os.path.join("**", args.pattern), recursive=True)
    else:
        paths = glob.glob(args.pattern)

    me = os.path.basename(os.path.abspath(__file__))
    paths = sorted(p for p in paths if os.path.isfile(p) and os.path.basename(p) != me)

    if not paths:
        print("No matching .py files found.")
        return

    print(f"Found {len(paths)} file(s). dry_run={args.dry_run}")
    for i, p in enumerate(paths, 1):
        print(f"\n=== [{i}/{len(paths)}] {p} ===")
        annotate(p, args.dry_run)
        if args.delay and i < len(paths):
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
