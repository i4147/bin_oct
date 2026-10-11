#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained Python 3 command-line script (intended to run under Termux on Android, so use the Termux-style `#!/data/data/com.termux/files/usr/bin/env python` shebang) that recursively scans the current working directory for `.lua` files and groups them into folders named after a normalized base name.

**Purpose:** Organize a loose collection of Lua files by moving each into a folder derived from its name, so that variants of the same script end up together.

**Inputs:**
- Command-line arguments via `argparse`, with a program description of "Group recursively collected Lua files into named folders."
- `--apply` (boolean flag): by default the script runs in dry-run mode and only prints the planned moves; with the flag, it actually moves files.
- The root to scan is the current working directory (`Path.cwd()`); the script itself must be excluded from the scan by comparing resolved paths.

**Name normalization rules (applied in this order):**
1. Take the file name and strip one or more trailing `.lua` extensions, case-insensitively.
2. Strip a trailing `_<digits>` suffix (e.g. `foo_2` → `foo`).
3. Trim whitespace and lowercase the result.
4. Replace runs of whitespace with `-`.
5. Replace any run of characters that are not word characters, `.`, or `-` with `-`.
6. Collapse repeated `-` into one.
7. Strip leading/trailing `-`, `.`, and `_`; if the result is empty, use `ungrouped`.

**Behavior:**
- Use `pathlib.Path` throughout and the standard library only (`argparse`, `re`, `shutil`, `collections.defaultdict`, `pathlib`). Include `from __future__ import annotations` and type hints using `list[Path]`-style annotations.
- Recursively find all `*.lua` files under the root (skip non-files and the script itself). Group the files by normalized name using a `defaultdict(list)`.
- For each group, the target folder is a subdirectory of the root named after the normalized key. Each file's destination is `folder / original_filename`.
- Skip files already inside their correct target folder (no move needed).
- If a destination already exists, do not overwrite: generate a unique name by appending `_1`, `_2`, … before the suffix, checking existence each time.
- Create target folders as needed (`mkdir` with parents and exist-ok semantics).
- Dry-run (default): print each planned move (source → destination) and a note that nothing was changed, and tell the user to rerun with `--apply`. With `--apply`, perform the moves with `shutil.move` and print each one.
- Print a summary line at the end with the number of files found and groups formed, in a clear, plain-text format.

**Error handling and edge cases:**
- Handle filenames that normalize to empty strings (fall back to `ungrouped`).
- Handle name collisions both within a group and against existing files.
- Handle symlinks and non-file entries by skipping them (`is_file()` check); compare resolved paths to avoid moving the script itself.
- If no `.lua` files are found, print a clear message and exit without error.
- Do not delete or overwrite any existing files.

**Execution:** Run as `python <script>` (or directly via the shebang) from the directory to organize; first run without flags to review, then rerun with `--apply` to commit the changes. Use a `main()` function guarded by `if __name__ == "__main__":`.
---"""

from __future__ import annotations

import argparse
import re
import shutil
from collections import defaultdict
from pathlib import Path


def normalize_name(path: Path) -> str:
    name = path.name
    name = re.sub(r"(?:\.lua)+$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"_\d+$", "", name)
    name = name.strip().lower()
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^\w.-]+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-._") or "ungrouped"


def unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination
    counter = 1
    while True:
        candidate = destination.with_name(f"{destination.stem}_{counter}{destination.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def find_lua_files(root: Path, script_path: Path) -> list[Path]:
    files = []
    for path in root.rglob("*.lua"):
        if not path.is_file():
            continue
        if path.resolve() == script_path.resolve():
            continue
        files.append(path)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description="Group recursively collected Lua files into named folders.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move files. Without this flag, only show planned moves.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="Directory to scan. Defaults to the current directory.",
    )
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    script_path = Path(__file__).resolve()
    if not root.is_dir():
        msg = f"Not a directory: {root}"
        raise SystemExit(msg)
    groups: defaultdict[str, list[Path]] = defaultdict(list)
    for path in find_lua_files(root, script_path):
        group_name = normalize_name(path)
        groups[group_name].append(path)
    if not groups:
        print("No Lua files found.")
        return
    for group_name, files in sorted(groups.items()):
        destination_dir = root / group_name
        print(f"\n[{group_name}]")
        if args.apply:
            destination_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(files):
            destination = destination_dir / source.name
            destination = unique_destination(destination)
            print(f"  {source.relative_to(root)} -> {destination.relative_to(root)}")
            if args.apply:
                shutil.move(str(source), str(destination))
    if not args.apply:
        print("\nDry run only. Use --apply to perform the moves.")


if __name__ == "__main__":
    main()
