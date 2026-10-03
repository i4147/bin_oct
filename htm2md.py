#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that batch-converts HTML/HTM files to Markdown using the external "rhtml2md" tool.
It should accept file and/or directory paths as command-line arguments, recursively collecting HTML files when a directory is given via a "get_files" helper, or default to scanning the current working directory if no arguments are provided.
For each matching file, it should run "rhtml2md" via a "runcmd" helper, write the resulting text to a sibling ".md" file, print a success confirmation, and log errors to stderr while continuing with other files; processing across all files should run in parallel using an "mpf" helper."""

from __future__ import annotations

import sys
from pathlib import Path

from dh import get_files, mpf, runcmd


def process_file(path) -> tuple[Path, bool]:
    path = Path(path)
    if path.suffix.lower() in {".html", ".htm"}:
        md_file = path.with_suffix(".md")
    else:
        return (path, False)
    try:
        _, txt, _ = runcmd(["rhtml2md", str(path)], show_output=False)
        md_file.write_text(txt, encoding="utf-8")
        print(f"✓ Converted: {path.name} -> {md_file.name}")
        return (md_file, True)
    except Exception as e:
        print(f"✗ Unexpected error converting {path}: {e}", file=sys.stderr)
        return (path, False)


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = []
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(get_files(p))
    else:
        files = get_files(cwd)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
