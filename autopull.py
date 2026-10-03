#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively scans the current working directory and its subdirectories to find all Git repositories (identified by the presence of a ".git" folder), then runs "git pull --ff-only" on each one found, printing progress messages for each repo it processes.
The script should stop descending into a directory once a Git repo is found there, gracefully skip directories it lacks permission to read, and print a warning if any pull fails without halting the overall process.
It takes no command-line inputs, operates on the current directory as the root, and outputs status messages to the console, finishing with a "Done." message."""

from __future__ import annotations

import subprocess
from pathlib import Path


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
