#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively scans the current directory for all Markdown files (.md and .markdown), then strips out Markdown image syntax and HTML image/badge elements (including standalone img tags, images wrapped in links, and images wrapped in paragraph tags) using regular expressions.
It should process files in parallel using a multiprocessing pool of 8 worker processes, overwrite each file only if its content changed, and print a per-file status message indicating whether it was updated, skipped, or errored, plus a summary of how many files were discovered before processing begins."""

import multiprocessing as mp
import re
from pathlib import Path

MD_IMAGE_PATTERN = re.compile(r"!\[.*?\]\(.*?\)")
HTML_BADGE_BLOCK_PATTERN = re.compile(
    r"<p\b[^>]*>[\s\S]*?<img\b[\s\S]*?</p>|"
    r"<a\b[^>]*>\s*<img\b[\s\S]*?</a>|"
    r"<img\b[^>]*\/?>",
    re.IGNORECASE,
)


def clean_file(path: Path):
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        cleaned_content = MD_IMAGE_PATTERN.sub("", content)
        cleaned_content = HTML_BADGE_BLOCK_PATTERN.sub("", cleaned_content)
        if content != cleaned_content:
            path.write_text(cleaned_content, encoding="utf-8")
            return f"Updated: {path}"
        return f"Skipped (No changes): {path}"
    except Exception as e:
        return f"Error processing {path}: {e}"


def main():
    target_dir = Path(".")
    md_files = list(target_dir.rglob("*.md")) + list(target_dir.rglob("*.markdown"))
    if not md_files:
        print("No markdown files discovered in the current path subtree.")
        return
    print(f"Discovered {len(md_files)} files. Spawning 8 worker processes...")
    with mp.Pool(processes=8) as pool:
        results = []
        for path in md_files:
            async_res = pool.apply_async(clean_file, args=(path,))
            results.append(async_res)
        for res in results:
            print(res.get())


if __name__ == "__main__":
    main()
