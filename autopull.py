#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory and all of its subdirectories to find every Git repository it contains, then runs a fast-forward-only pull on each one it discovers. The tool should treat a directory as a Git repository when it contains a Git metadata folder, stop descending further into that repository once it has been handled, and skip any subdirectories it cannot access without crashing. For each repository, print a clear progress message showing its path before pulling. If a pull fails (for example, because of local changes, divergent history, or network problems), report a warning that identifies the affected repository, but continue processing the remaining repositories rather than aborting. When the scan is complete, print a final message indicating that the run has finished, and exit with a standard success status code. The script should require no command-line arguments and no user interaction, and should produce readable, plain-text console output that makes it easy to see which repositories were updated and which ones failed.
---"""

from __future__ import annotations
from pathlib import Path
import subprocess


def is_git_repo(path: Path) -> bool:
    return (path / ".git").is_dir()


def git_pull(repo_path: Path) -> None:
    print(f"\n==> Pulling in repo: {repo_path}")
    try:
        subprocess.run(["git", "-C", str(repo_path), "pull", "--ff-only"], check=True)
    except subprocess.CalledProcessError:
        print(f"⚠️  git pull failed in: {repo_path}")


def walk_and_pull(path: Path) -> None:
    if is_git_repo(path):
        git_pull(path)
        return
    try:
        for item in path.iterdir():
            if item.is_dir() and item.name != ".git":
                walk_and_pull(item)
    except PermissionError:
        pass


def main() -> None:
    root = Path.cwd()
    walk_and_pull(root)
    print("\nDone.")


if __name__ == "__main__":
    raise SystemExit(main())
