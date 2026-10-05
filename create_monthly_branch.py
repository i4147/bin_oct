#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that automates monthly git branch creation for a repository located at ~/bin.
It should derive a branch name from the current month and year (e.g., "september_2026"), check both local and remote branches to see if it already exists, and skip creation if so.
If the branch doesn't exist, it should fetch all remotes, checkout and pull the main branch, then create and push the new monthly branch, printing status messages throughout using subprocess calls to git commands."""

from __future__ import annotations
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_PATH = Path.home() / "bin"
MAIN_BRANCH = "main"


def get_branch_name() -> str:
    now = datetime.now()
    return f"{now.strftime('%B').lower()}_{now.year}"


def branch_exists(branch_name: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
        )
        if branch_name in result.stdout:
            return True
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch_name],
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
        )
        return f"refs/heads/{branch_name}" in result.stdout
    except Exception:
        return False


def create_monthly_branch() -> bool:
    branch_name = get_branch_name()
    print(f"Creating branch for {branch_name}...")
    if branch_exists(branch_name):
        print(f"✓ Branch '{branch_name}' already exists")
        return True
    try:
        subprocess.run(["git", "fetch", "--all"], cwd=REPO_PATH, check=True, capture_output=True)
        subprocess.run(
            ["git", "checkout", MAIN_BRANCH],
            cwd=REPO_PATH,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "pull"], cwd=REPO_PATH, check=True, capture_output=True)
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=REPO_PATH,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=REPO_PATH,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", MAIN_BRANCH],
            cwd=REPO_PATH,
            check=True,
            capture_output=True,
        )
        print(f"✓ Created and pushed branch: {branch_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e.stderr.decode() if e.stderr else str(e)}")
        return False


if __name__ == "__main__":
    if not (REPO_PATH / ".git").exists():
        print(f"Error: {REPO_PATH} is not a Git repository")
        sys.exit(1)
    success = create_monthly_branch()
    sys.exit(0 if success else 1)
