#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that recursively processes text files (either passed as CLI arguments or discovered via a helper `get_nobinary` function that lists non-binary files under the current directory) and replaces common HTML entities (like `&lt;`, `&amp;`, `&nbsp;`, `&mdash;`, etc.) with their corresponding Unicode characters using a precompiled regex and lookup table.
It should read each file as UTF-8, only rewrite the file if content actually changed, use `multiprocessing` to process files in parallel for performance, and track/report which files were changed versus which raised errors during processing."""

from __future__ import annotations
import multiprocessing as mp
import re
import sys
from pathlib import Path
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
