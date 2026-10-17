#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations
import argparse
from concurrent.futures import InterpreterPoolExecutor
from pathlib import Path
import re

from dh import SHEBANG_MAP, is_binary


SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".idea",
    ".vscode",
}


def normalize(name: str) -> str:
    return re.sub(r"[\d.]+$", "", name)


KNOWN = {normalize(k) for k in SHEBANG_MAP}


def process(p: Path) -> tuple[str, Path] | None:
    if is_binary(p):
        return None
    try:
        with p.open("rb") as f:
            first = f.readline()
    except OSError:
        return None
    if not first.startswith(b"#!"):
        return None
    try:
        line = first.decode("utf-8", "replace").strip()
    except Exception:
        return None
    parts = line[2:].strip().split()
    if not parts:
        return None
    exe = parts[0]
    if exe == "env" or exe.endswith("/env"):
        if len(parts) < 2:
            return None
        exe = parts[1]
    base = exe.rsplit("/", 1)[-1]
    lang = normalize(base)
    if lang not in KNOWN:
        return None
    return lang, p


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    files: list[Path] = []
    for p in Path().rglob("*"):
        if p.is_symlink() or not p.is_file():
            continue
        if p.suffix:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        files.append(p)
    counts: dict[str, int] = {}
    with InterpreterPoolExecutor() as ex:
        for res in ex.map(process, files):
            if res is None:
                continue
            lang, path = res
            counts[lang] = counts.get(lang, 0) + 1
            if args.verbose:
                print(path)
    if not counts:
        print("nothing found")
        return
    for name, cnt in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"{name:<10}{cnt:>5}")


if __name__ == "__main__":
    main()
