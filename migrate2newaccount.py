#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that migrates all Git repositories found in the current directory to a new GitHub account under a specified username (e.g., "i4147"), skipping a predefined ignore list such as "cpython", "neovim-source", and ".git".
For each valid repository, it should stage and commit any uncommitted changes with a "migration sync" message, create a new private repository on GitHub using the "gh" CLI, update the repository's remote origin URL to point to the new account via SSH, and push all branches and tags to the new remote.
The script should use "os" for directory traversal and "subprocess" to execute Git and GitHub CLI commands, suppressing their output, and should safely change directories in and out of each repository during processing."""

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
        status = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True
        )
        if status.stdout.strip():
            subprocess.run(
                ["git", "commit", "-m", "migration sync"], capture_output=True
            )
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
