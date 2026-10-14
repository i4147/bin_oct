#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts HTML files into Markdown files using an external HTML-to-Markdown command-line converter. The tool should accept zero or more command-line arguments, where each argument can be either a single file path or a directory path. When no arguments are provided, it should default to scanning the current working directory. For directories, it should discover all files within them, while for individual files it should process them directly.
Only files with an HTML extension (.html or .htm, case-insensitive) should be converted. Each converted file should produce a Markdown file placed alongside the original, sharing the same base name but with a .md extension. Non-HTML files should be skipped without error. The conversion should be performed by invoking the external converter on each file, capturing its output, and writing that output to the new Markdown file using UTF-8 encoding. Conversion should be applied to multiple files in a parallel or batched manner using a mapping utility that processes each file and collects results.
For each file, the tool should print a concise success message showing the original and new file names when conversion succeeds. If an error occurs, it should print a descriptive error message including the file path and the exception details to the standard error stream, and continue processing remaining files without stopping the entire run. The script should be runnable directly from the command line and should handle missing or unusual inputs gracefully without crashing.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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
