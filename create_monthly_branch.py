#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that automates creating a monthly git branch in a local repository. The script should target a fixed repository location in the user's home directory and a main branch named "main". It should derive the branch name from the current date in the form of the lowercase full month name followed by an underscore and the four-digit year (for example, "october_2026").
When run, the script should first check whether a branch with that name already exists, either locally or on the remote named "origin". If it already exists, the script should report this clearly to the user and exit successfully without making changes. If it does not exist, the script should ensure the repository is up to date with the main branch, then create the new monthly branch from main and push it to the remote, setting up upstream tracking. Each step should print concise, human-readable progress messages with clear success and failure indicators. If any git operation fails, the script should stop, report the error in a helpful way, and return a non-zero exit status. The script should handle unexpected exceptions gracefully rather than crashing with a raw traceback, and it should exit with status zero on success and non-zero on failure.
---"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import subprocess
import sys

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
