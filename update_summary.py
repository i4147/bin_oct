#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that regenerates a SUMMARY.md table of contents by recursively scanning the current working directory for all Markdown (.md) files.
It should preserve the existing header lines at the top of SUMMARY.md (everything before the first list item), then rebuild the list of entries by sorting the found files by relative path, converting each filename into a human-readable title (replacing underscores and slashes with spaces and applying title case), and writing them as Markdown links in the format "- [Title](./relative/path.md)".
After writing the updated file, it should print a message stating how many chapters were added."""

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
