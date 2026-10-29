#!/data/data/com.termux/files/usr/bin/env python
import shutil
import sys
from pathlib import Path

from dh import SKIP_DIRS, should_skip
from rignore import walk as _walk

JUNK_FILE = Path("/sdcard/data/junk")

JUNK_SUFFIXES = (
    ".pyc",
    ".tmp",
    ".log",
    ".bak",
    ".cache.json",
    ".exe",
    ".bat",
    ".dll",
    ".dylib",
    ".pyd",
    ".lnk",
    ".msi",
)

GIT_META_FILES = frozenset({".gitkeep", ".gitmodules", ".gitignore"})
GIT_META_DIRS = frozenset({".github"})


def load_junk_names(path: Path = JUNK_FILE) -> frozenset[str]:
    """Load the junk filename list from `path` (one name per line)."""
    try:
        with path.open(encoding="utf-8") as fh:
            return frozenset(line.strip().lower() for line in fh if line.strip())
    except OSError as exc:
        print(f"warning: could not read {path}: {exc}", file=sys.stderr)
        return frozenset()


_git_cache: dict[Path, bool] = {}


def in_git_repo(path: Path) -> bool:
    """True if `path` lives inside a git working tree.

    Walks up the parent chain looking for a `.git` entry (dir *or* file, so
    worktrees and submodules count).  Results are cached per directory since
    `.git` entries don't appear/disappear while this script runs.
    """
    chain: list[Path] = []
    result = False
    for parent in path.parents:
        cached = _git_cache.get(parent)
        if cached is not None:
            result = cached
            break
        chain.append(parent)
        if (parent / ".git").exists():
            result = True
            break
    for parent in chain:
        _git_cache[parent] = result
    return result


def remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def main() -> int:
    cwd = Path.cwd()
    junk_names = load_junk_names()
    removed_count = 0

    for path in _walk(cwd):
        if not path.exists() or path.is_symlink() or ".git" in path.parts:
            continue

        loname = path.name.lower()

        if loname in GIT_META_FILES or (loname in GIT_META_DIRS and path.is_dir()):
            if not in_git_repo(path):
                remove(path)
                removed_count += 1
                print(f"{path.name} removed")
            continue

        if path.is_file() and (loname.endswith(JUNK_SUFFIXES) or loname in junk_names):
            path.unlink()
            removed_count += 1
            print(f"{path.name} removed")
            continue

        if path.is_dir() and loname == "licenses" and "dist-info" in path.parent.name:
            shutil.rmtree(path)
            removed_count += 1
            print(f"{path.name} removed")
            continue

    if removed_count:
        print(f"\n{removed_count} item(s) removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
