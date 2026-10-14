#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that migrates a collection of local Git repositories to a new GitHub account. The script should run from a parent directory containing multiple project folders, skip a configurable set of excluded folder names (such as large upstream source trees and version-control metadata directories), and process each remaining subdirectory that is an initialized Git repository.
For each eligible repository, the script should:
- Stage all current changes and create a single sync commit only if there are uncommitted modifications.
- Create a private repository under the target GitHub account with the same name as the local folder, using the GitHub command-line tool.
- Repoint the repository's origin remote to the new account's SSH address.
- Push all local branches and all tags to the new origin, setting upstream tracking.
The script should handle errors gracefully so that a failure in one repository (for example, a repository that already exists on GitHub or a push that is rejected) does not stop processing of the remaining repositories. It should return to the parent directory after each repository is handled, skip non-Git folders without treating them as failures, and conclude with a summary report listing which repositories were migrated successfully and which encountered problems. The target account name should be a single, easily changeable setting at the top of the script, and command output should be captured so the terminal stays readable, while still surfacing a clear log of each step's outcome.
---"""

from __future__ import annotations
import os
import subprocess

NEW_USER = "i4147"
IGNORE = {"cpython", "neovim-source", ".git"}


def migrate():
    for repo in [d for d in os.listdir(".") if os.path.isdir(d) and d not in IGNORE]:
        os.chdir(repo)
        if not os.path.exists(".git"):
            os.chdir("..")
            continue
        subprocess.run(["git", "add", "."], capture_output=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "commit", "-m", "migration sync"], capture_output=True)
        subprocess.run(
            ["gh", "repo", "create", f"{NEW_USER}/{repo}", "--private"],
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "remote",
                "set-url",
                "origin",
                f"git@github.com:{NEW_USER}/{repo}.git",
            ],
            capture_output=True,
        )
        subprocess.run(["git", "push", "-u", "origin", "--all"], capture_output=True)
        subprocess.run(["git", "push", "-u", "origin", "--tags"], capture_output=True)
        os.chdir("..")


if __name__ == "__main__":
    migrate()
