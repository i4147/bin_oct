#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that moves every top-level subdirectory from a user-specified source directory into a user-specified destination directory. The script should accept the source and destination paths as input (for example, via command-line arguments), and it should validate them before doing anything: both must exist and be directories, and they must not be the same location. If either check fails, the script should report a clear, emoji-friendly error message and exit without changing any files.
Once validation passes, the script should display the resolved source and destination paths for the user's reference, then list the immediate subdirectories of the source in a consistent, sorted order. If the source contains no subdirectories, it should inform the user with a warning and stop gracefully.
Before moving anything, the script should check whether the destination already contains a subdirectory with the same name as one in the source. Such conflicts must be handled safely: the script should skip the conflicting folder and report it rather than overwriting or merging existing data. All non-conflicting subdirectories should be moved to the destination, and the script should report each successful move as well as each skipped item, so the user always knows what happened.
Only immediate child directories are in scope; regular files and nested subfolders within those directories should be carried along intact, and files directly inside the source directory should be left untouched. The script should handle errors on individual moves (such as permission problems) gracefully, continuing with the remaining items and reporting the failure instead of crashing.
At the end, the script should print a concise summary showing how many subdirectories were moved, how many were skipped due to conflicts, and how many failed. The overall output should be clear, readable, and user-friendly, with status indicators for each action, and the script should exit with an appropriate status code reflecting success or failure.
---"""

from __future__ import annotations
from pathlib import Path
from shutil import move
import sys


def validate_dirs(source: Path, dest: Path) -> bool:
    if not source.is_dir():
        print(f"❌ Source directory does not exist: {source}")
        return False
    if not dest.is_dir():
        print(f"❌ Destination directory does not exist: {dest}")
        return False
    if source == dest:
        print("❌ Source and destination cannot be the same directory")
        return False
    return True


def get_top_level_subdirs(directory: Path) -> list[Path]:
    subdirs = [p for p in directory.iterdir() if p.is_dir()]
    return sorted(subdirs)


def move_subdirs(source: Path, dest: Path) -> None:
    print(f"📂 Source directory: {source.resolve()}")
    print(f"📂 Destination directory: {dest.resolve()}")
    print("-" * 40)
    source_subdirs = get_top_level_subdirs(source)
    if not source_subdirs:
        print("⚠️  No subdirectories found in source")
        return
    dest_subdir_names = {p.name for p in get_top_level_subdirs(dest)}
    moved = []
    skipped = []
    for subdir in source_subdirs:
        if subdir.name in dest_subdir_names:
            print(f"⏭️  SKIP: {subdir.name} (already exists in destination)")
            skipped.append(subdir.name)
        else:
            try:
                new_path = dest / subdir.name
                print(f"➡️  MOVE: {subdir.name}")
                print(f"   From: {subdir.resolve()}")
                print(f"   To:   {new_path.resolve()}")
                move(str(subdir), str(new_path))
                moved.append(subdir.name)
                print(f"   ✅ Success")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    print("-" * 40)
    print(f"\n📊 Summary:")
    print(f"✅ Moved: {len(moved)}")
    if moved:
        for name in moved:
            print(f"   • {name}")
    print(f"⏭️  Skipped: {len(skipped)}")
    if skipped:
        for name in skipped:
            print(f"   • {name}")


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python dir_mver.py <source_dir> <dest_dir>")
        print("Example: python dir_mver.py ~/repos/projects ~/isaac")
        sys.exit(1)
    source = Path(sys.argv[1]).expanduser().resolve()
    dest = Path(sys.argv[2]).expanduser().resolve()
    if not validate_dirs(source, dest):
        sys.exit(1)
    move_subdirs(source, dest)


if __name__ == "__main__":
    raise SystemExit(main())
