#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree and reports which files are executable scripts whose interpreter is unrecognized or unusual. The tool should accept a root directory path as input and recursively walk through it, skipping common non-source directories such as version control folders, dependency caches, virtual environments, build outputs, and editor metadata folders.
For each regular file, the script should quickly determine whether it is a binary file and ignore it if so. For text files, it should read only the first line and check whether it is a shebang line. When a shebang is found, the script should extract the interpreter name, correctly handling both direct interpreter paths and the indirect form that routes through the `env` command, and reduce it to its base program name. Versioned suffixes on interpreter names (such as trailing digits or version numbers) should be normalized so that variants like "python3.11" and "python" are treated as the same interpreter family.
The script should compare each detected interpreter against a built-in table of known interpreters and their expected shebang forms. It should produce a report listing files whose shebang refers to an interpreter that is not in the known set, along with each file's relative path, the raw shebang line, and the interpreter it resolves to. Files with no shebang, binary files, and unreadable files should be silently skipped.
The processing of individual files should be parallelized across multiple workers to handle large directory trees efficiently, and the final output should be clearly organized and sorted by path. The script should be runnable from the command line with the root directory as an argument, provide helpful usage information, and exit with a meaningful status code indicating whether any suspicious shebangs were found.
---"""

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
