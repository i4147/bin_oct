#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a user-specified directory tree and identifies operating-system and platform junk or system-generated files and folders that should typically be excluded from backups, archives, or cleanup operations. The script should accept a root directory path from the user, recursively walk its contents, and flag or report every item whose name matches a predefined set of known macOS metadata artifacts (such as Finder and Spotlight leftovers, resource-fork files, and trash folders) and known Windows system or executable-style artifacts (such as thumbnail caches, desktop configuration files, recycle bin entries, and certain binary or installer extensions). Matching should support both exact filename matches and wildcard-style patterns, including prefix and suffix rules, and should apply consistently to both files and directories.
The script should produce a clear, human-readable summary listing each matched path along with its type and size where applicable, plus overall totals for count and combined size. It should offer a dry-run mode that only reports findings, and an optional mode that actually removes the matched items after confirmation. Handle permission errors, broken symbolic links, and unreadable paths gracefully by logging a warning and continuing. Allow the user to choose which platform pattern sets to apply (macOS, Windows, or both), and let the user add custom patterns from the command line. Provide helpful command-line usage information, validate inputs before scanning, and exit with meaningful status codes for success, invalid input, and partial failures.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import fsz

DARWIN_PATTERNS = {
    ".DS_Store",
    ".AppleDouble",
    ".LSOverride",
    ".TemporaryItems",
    ".Spotlight-V100",
    ".Trashes",
    "._*",
    ".com.apple.*",
}
WINDOWS_PATTERNS = {
    "*.exe",
    "*.dll",
    "*.sys",
    "*.bat",
    "*.cmd",
    "*.com",
    "*.msi",
    "*.scr",
    "*.lnk",
    "*.pyd",
    "*.dylib",
    "Thumbs.db",
    "desktop.ini",
    "$RECYCLE.BIN",
}
ALL_PATTERNS = DARWIN_PATTERNS | WINDOWS_PATTERNS


def matches_pattern(path: Path, patterns: set) -> bool:
    name = path.name
    for pattern in patterns:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif pattern.startswith("._"):
            if name.startswith("._"):
                return True
        elif pattern.startswith(".") and pattern != ".DS_Store":
            if name == pattern or (path.is_dir() and name == pattern):
                return True
        elif name == pattern or path.name.startswith(pattern.split("*")[0]):
            return True
    return False


def walk_directory(root_dir: Path):
    try:
        for entry in root_dir.iterdir():
            yield entry
            if entry.is_dir():
                yield from walk_directory(entry)
    except (OSError, PermissionError) as e:
        print(f"Error accessing {root_dir}: {e}", file=sys.stderr)


def process_path(path: Path) -> tuple[str, int]:
    try:
        if path.is_file():
            size = path.stat().st_size
            path.unlink()
            return (str(path), size)
        elif path.is_dir():
            total_size = 0
            for path in walk_directory(path):
                if path.is_file():
                    total_size += path.stat().st_size
            import shutil

            shutil.rmtree(path)
            return (str(path), total_size)
    except (OSError, PermissionError) as e:
        print(f"Error deleting {path}: {e}", file=sys.stderr)
    return (str(path), 0)


def find_and_remove_files(root_dir: Path | None = None) -> dict:
    if root_dir is None:
        root_dir = Path.cwd()
    else:
        root_dir = Path(root_dir)
    if not root_dir.exists():
        print(f"Error: {root_dir} does not exist", file=sys.stderr)
        return {}
    matching_paths = []
    for path in walk_directory(root_dir):
        if matches_pattern(path, ALL_PATTERNS):
            matching_paths.append(path)
    if not matching_paths:
        return {"files_removed": 0, "total_freed_bytes": 0, "total_freed_human": "0 B"}
    results = []
    for path in matching_paths:
        print(f"Removing: {path}")
        result = process_path(path)
        results.append(result)
    total_freed = sum((size for _, size in results))
    successful = sum((1 for _, size in results if size > 0))
    stats = {
        "files_removed": successful,
        "total_freed_bytes": total_freed,
        "total_freed_human": fsz(total_freed),
        "details": results,
    }
    return stats


def main():
    stats = find_and_remove_files(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
