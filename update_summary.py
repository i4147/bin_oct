#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory and all of its subdirectories for Markdown files, then regenerates a table-of-contents file named SUMMARY.md in the same directory. The script should preserve the existing header section of SUMMARY.md (the leading non-empty lines that appear before the first list entry) and rewrite everything after it with a fresh, alphabetically sorted list of links to every discovered Markdown file. Each link should use a human-readable title derived from the file name (replacing underscores and path separators with spaces and applying title case) and a relative path starting from the current directory. The script should read and write all files using UTF-8 encoding, handle the case where the existing SUMMARY.md has no header lines, and print a short confirmation message to the console stating how many chapters were written. It should run as a standalone command-line tool when executed directly.
---"""

from __future__ import annotations
from pathlib import Path


def find_md_files():
    cwd = Path.cwd()
    md_files = []
    for path in cwd.rglob("*.md"):
        rel_path = path.relative_to(cwd)
        md_files.append(rel_path)
    return md_files


def update_summary() -> None:
    md_files = find_md_files()
    md_files.sort()
    summarymd = Path("SUMMARY.md")
    lines = summarymd.read_text(encoding="utf-8").splitlines()
    header = []
    for line in lines:
        if line.strip() and not line.strip().startswith("- ["):
            header.append(line)
        else:
            break
    new_entries = []
    for md_file in md_files:
        title = md_file.stem.replace("_", " ").replace("/", " ").title()
        entry = f"- [{title}](./{md_file})\n"
        new_entries.append(entry)
    with summarymd.open("w", encoding="utf-8") as f:
        f.writelines(header)
        f.write("\n")
        f.writelines(new_entries)
    print(f"Updated SUMMARY.md with {len(new_entries)} chapters.")


if __name__ == "__main__":
    update_summary()
