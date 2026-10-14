#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory of text-based files and decodes common HTML character entities in place, so that the files contain the actual characters instead of their escaped forms. The script should accept a target folder (or a single file) as input, process every relevant file it finds, and leave files untouched when no entity replacements are needed.
Key behaviors:
- Recognize a fixed set of common HTML entities (such as ampersand, angle brackets, quotes, non-breaking space, currency symbols, copyright and registered marks, dashes, ellipsis, and typographic quotes) and replace each with its corresponding character.
- Read and write files using UTF-8 encoding, and only rewrite a file when its content actually changes.
- Handle large sets of files efficiently by distributing the work across multiple worker processes, and make sure the parent process collects results safely.
- Skip or gracefully report files that cannot be read, decoded, or written, without stopping the entire run.
- Provide a summary at the end showing how many files were scanned, how many were modified, and any errors encountered.
- Allow the user to control the number of worker processes, and offer a dry-run option that reports which files would change without modifying them.
- Include a helper that excludes binary files from processing, so only plain text content is altered.
- Print clear, concise progress and status messages to the console, and return a non-zero exit status if any errors occurred.
The script should be a standalone command-line tool, runnable from a terminal with paths supplied as arguments, and should be written so that it is safe to run repeatedly (idempotent) on the same set of files.
---"""

from __future__ import annotations
import multiprocessing as mp
from pathlib import Path
import re
import sys
from dh import get_nobinary

HTML_ENTITIES = {
    "&lt;": "<",
    "&gt;": ">",
    "&amp;": "&",
    "&quot;": '"',
    "&apos;": "'",
    "&nbsp;": " ",
    "&copy;": "©",
    "&reg;": "®",
    "&euro;": "€",
    "&pound;": "£",
    "&yen;": "¥",
    "&dollar;": "$",
    "&cent;": "¢",
    "&sect;": "§",
    "&dagger;": "†",
    "&Dagger;": "‡",
    "&hellip;": "…",
    "&mdash;": "—",
    "&ndash;": "–",
    "&lsquo;": "'",
    "&rsquo;": "'",
    "&ldquo;": '"',
    "&rdquo;": '"',
}
ENTITY_PATTERN = re.compile("|".join(re.escape(k) for k in HTML_ENTITIES))


def replace_entities(text: str) -> str:
    def replacer(match) -> str:
        return HTML_ENTITIES[match.group(0)]

    return ENTITY_PATTERN.sub(replacer, text)


def process_file(path: Path) -> tuple[Path, bool, str]:
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        new_content = replace_entities(content)
        changed = content != new_content
        if changed:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
        return (path, changed, "")
    except Exception as e:
        return (path, False, str(e))


def main() -> None:
    cwd = Path.cwd().resolve()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_nobinary(cwd)
    changed_files = []
    error_files = []
    with mp.Pool(processes=8) as pool:
        results = pool.map(process_file, files)
        for path, changed, error in results:
            if error:
                error_files.append((path, error))
            elif changed:
                changed_files.append(path)
    print("\n" + "=" * 40)
    print("SUMMARY")
    print("-" * 40)
    if changed_files:
        print(f"\n✅ Modified {len(changed_files)} file(s):")
        for f in changed_files:
            p = Path(f).resolve()
            print(f"  - {p.relative_to(cwd)}")
    else:
        print("\n✅ No files were modified")
    if error_files:
        print(f"\n❌ Errors in {len(error_files)} file(s):")
        for f, err in error_files:
            p = Path(f).resolve()
            print(f"  - {p.relative_to(cwd)}: {err}")
    print(f"   Modified: {len(changed_files)}")
    print(f"   Errors: {len(error_files)}")


if __name__ == "__main__":
    raise SystemExit(main())
