#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with the following specification:

Create a Python 3 script for Termux (Android) that automates creating a monthly git branch in a local repository located at the user's home directory under a `bin` folder. The script must begin with a Termux-specific shebang line pointing to the Termux Python interpreter and use postponed annotation evaluation (`from __future__ import annotations`). It should use only the standard library: `subprocess`, `sys`, `datetime`, and `pathlib`. Define module-level constants for the repository path (the `bin` directory inside the user's home, resolved via `Path.home()`) and the main branch name (`main`).

Implement these functions:

1. `get_branch_name() -> str`: returns the current month's name in lowercase followed by an underscore and the four-digit year (for example, a name of the form `<month>_<year>`), derived from the current local date/time.

2. `branch_exists(branch_name: str) -> bool`: returns True if the branch exists either locally or on the remote. First run `git branch --list <name>` in the repository directory with captured text output and check whether the name appears in stdout. If not found locally, run `git ls-remote --heads origin <name>` in the same directory and check whether the string `refs/heads/<name>` appears in stdout. Wrap the whole check in a broad exception handler that returns False on any error. Use `capture_output=True` and `text=True` for all subprocess calls.

3. `create_monthly_branch() -> bool`: compute the branch name, print `Creating branch for <name>...`, and if the branch already exists print a success line with a check mark (`✓ Branch '<name>' already exists`) and return True. Otherwise, inside a try block: run `git fetch --all` (with `check=True` and captured output), run `git checkout <MAIN_BRANCH>` (with `check=True` and captured output), then pull the latest changes from the remote for the main branch, create and switch to the new branch using `git checkout -b`, push it to origin with upstream tracking (`git push -u origin <name>`), and print a success message with a check mark on completion. Return True on success. Catch `subprocess.CalledProcessError` to print an error message that includes the failing command's stderr (decoded safely, handling None), and return False. Catch any other exception with a generic error message and return False.

4. A `main()` function that calls `create_monthly_branch()` and exits with status 0 on success or 1 on failure using `sys.exit`, and an `if __name__ == "__main__":` guard invoking it.

Behavioral requirements and edge cases to honor: the script must not create duplicate branches if one already exists locally or remotely; it must operate entirely within the repository directory via the `cwd` argument rather than changing the process working directory; all git failures must be reported to the user with useful stderr output rather than crashing with an unhandled traceback; and the month name must be lowercase regardless of locale-specific capitalization. Output messages should be concise, plain text, and use the check mark symbol only for success lines. The script should be runnable directly as an executable file with no command-line arguments required.

Deliver the complete script as a single file.
---"""

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
