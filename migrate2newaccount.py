#!/data/data/com.termux/files/usr/bin/env python

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
