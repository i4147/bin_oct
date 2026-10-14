#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree for Lua script files and reorganizes them into groups based on a normalized base name. The tool should accept a root directory path as its main input (with an option to run in a preview or dry-run mode), locate all Lua files recursively while ignoring the script itself, and derive a clean, consistent group name for each file by stripping Lua-related extensions, trailing numeric version suffixes, and unsafe characters, then converting the result to a lowercase, hyphen-separated slug with a fallback name for files that yield nothing usable.
Files sharing the same normalized name should be collected into a dedicated folder under the root, and each file should be moved into its group folder without overwriting existing files; when a name collision occurs, the tool should append an incrementing numeric suffix to the filename instead. The script should report clearly what it did or would do, including each planned or completed move, and handle missing paths, permission issues, and unexpected filesystem errors gracefully with informative messages and a sensible exit status. Design the command-line interface so the user can easily specify the target directory and toggle preview mode, and keep the overall behavior safe, predictable, and idempotent so that running it repeatedly does not corrupt or duplicate the organized structure.
---"""

from __future__ import annotations
import argparse
from collections import defaultdict
from pathlib import Path
import re
import shutil


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
