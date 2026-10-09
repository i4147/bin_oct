#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that recursively walks the current working directory and all its subdirectories to find every folder containing a .git directory, identifying it as a Git repository.
For each repository found, it should print the repository path and run "git restore ." to discard local uncommitted changes, catching and printing a warning message if the command fails rather than stopping execution.
The script takes no command-line inputs, operates directly on the filesystem starting from the current directory, and prints a "Done." message once all repositories have been processed.
"""

from __future__ import annotations
import os
import subprocess
from pathlib import Path


def is_git_repo(path: Path) -> bool:
    return (path / ".git").is_dir()


def git_pull(repo_path: Path) -> None:
    print(f"\n==> Pulling in repo: {repo_path}")
    try:
        subprocess.run(["git", "-C", str(repo_path), "restore", "."], check=True)
    except subprocess.CalledProcessError:
        print(f"⚠️  git pull failed in: {repo_path}")


def main() -> None:
    root = Path.cwd()
    for dirpath, _dirnames, _filenames in os.walk(root):
        current = Path(dirpath)
        if is_git_repo(current):
            git_pull(current)
    print("\nDone.")


if __name__ == "__main__":
    raise SystemExit(main())
