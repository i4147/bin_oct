#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that organizes the files in a given directory by their file extension. The script should recursively scan the specified root folder and all of its subfolders, skipping version-control metadata (any `.git` directory) and `.gitignore` files. For every regular file it encounters, it should determine the file's extension (case-insensitively), treating files without an extension as belonging to a special "no extension" group. It should gather statistics for each extension group, including the number of files and the combined size in bytes, along with the list of files that belong to it.
Based on this analysis, the script should create a top-level subfolder in the root directory for each extension group (reusing it if it already exists) and move the matching files into their corresponding folder, avoiding overwriting existing files and handling name collisions sensibly. Files already located directly inside their correct extension folder should be left in place. The script should be safe to run in the working directory it is given, should not disturb the version-control metadata, and should tolerate errors on individual files (such as permission issues or files that disappear mid-run) without aborting the entire operation.
Upon completion, the script should print or return a concise summary report listing each extension group, its file count, and its total size in a human-readable format, sorted in a sensible order, along with a total for all processed files. The tool should accept the target directory as input (defaulting to the current working directory) and be written with clear, maintainable structure and helpful messages for the user.
---"""

from __future__ import annotations
import contextlib
from pathlib import Path
import shutil
from dh import gsz


def folderize_by_extension(cwd: Path):
    root_path = Path(cwd)
    extension_stats = {}
    for path in root_path.rglob("*"):
        if path.name == ".gitignore":
            continue
        if ".git" in path.parts:
            continue
        if path.is_file():
            ext = path.suffix.lower()[1:] if path.suffix else "no_extension"
            size = path.stat().st_size
            if ext not in extension_stats:
                extension_stats[ext] = {"count": 0, "total_size": 0, "files": []}
            extension_stats[ext]["count"] += 1
            extension_stats[ext]["total_size"] += size
            extension_stats[ext]["files"].append(path)
    created_dirs = set()
    for ext, stats in extension_stats.items():
        target_dir = root_path / ext
        target_dir.mkdir(exist_ok=True)
        created_dirs.add(ext)
        for path in stats["files"]:
            if path.parent == target_dir:
                continue
            target_path = target_dir / path.name
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{path.stem}_{counter}{path.suffix}"
                counter += 1
            with contextlib.suppress(BaseException):
                shutil.move(str(path), str(target_path))
    for dir_path in sorted(root_path.glob("**/*"), key=lambda p: len(p.parts), reverse=True):
        if dir_path.is_dir() and dir_path != root_path:
            with contextlib.suppress(OSError):
                dir_path.rmdir()
    total_files = 0
    total_size = 0
    for ext in sorted(extension_stats.keys()):
        stats = extension_stats[ext]
        total_files += stats["count"]
        total_size += stats["total_size"]
        ext_display = ext or "no_extension"
        size_str = gsz(stats["total_size"])
        print(f"{ext_display:<15} : {stats['count']:4} file{'s' if stats['count'] != 1 else ' '}  {size_str:>8}")
    print("-" * 40)
    print(f"{'TOTAL':<15} : {total_files:4} files  {gsz(total_size):>8}")
    print("=" * 40)
    return created_dirs, extension_stats


if __name__ == "__main__":
    target_dir = Path.cwd()
    created_dirs, stats = folderize_by_extension(target_dir)
    print(f"\nCreated {len(created_dirs)} extension folders.")
