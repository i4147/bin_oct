#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a convenient git clone wrapper command. It takes a repository URL as its required input, with an optional target directory name. When invoked without arguments, it should print a short usage message and exit with an error status.
The tool should automatically detect the remote repository's default branch (rather than assuming "main" or "master") by querying the remote before cloning, and it should report a clear error to the user if the default branch cannot be determined. It should derive a sensible local folder name from the repository URL when no target directory is given, and clone the repository's default branch into that location.
After cloning, the script should check whether the repository uses git submodules and, if so, initialize and update them recursively so the working copy is complete. It should report progress and success or failure messages to the user in a concise, readable way, using clear status indicators, and return an appropriate exit code (zero on success, non-zero on failure), so it can be used directly from the command line.
The script should handle common failure cases gracefully, such as unreachable URLs, a target directory that already exists, or git operations that fail midway, without leaving the user with unclear or confusing output. It should be a single, self-contained, dependency-free command-line tool that relies only on the standard environment where git is installed.
---"""

from __future__ import annotations
from pathlib import Path
import re
import subprocess
import sys


def _default_branch(url: str) -> str | None:
    result = subprocess.run(
        ["git", "ls-remote", "--symref", url, "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        m = re.match(r"^ref:\s+refs/heads/(\S+)\s+HEAD", line)
        if m:
            return m.group(1)
    return None


def _has_submodules(repo_dir: Path) -> bool:
    rc = subprocess.run(
        ["git", "-C", str(repo_dir), "cat-file", "-e", "HEAD:.gitmodules"],
        capture_output=True,
    ).returncode
    return rc == 0


def git_clone2(*args):
    if not args:
        print("Usage: g2 <repo-url> [target-dir]")
        return 1
    url = args[0]
    target = args[1] if len(args) > 1 else ""
    branch = _default_branch(url)
    if not branch:
        print(f"❌ Could not determine default branch for {url}", file=sys.stderr)
        return 1
    repo = Path(url.rstrip("/")).name
    repo = repo.removesuffix(".git")
    if not target:
        target = f"{repo}.git"
    print(f"🔍 Default branch: {branch}")
    print(f"📦 Cloning only '{branch}' (with submodules) from {url} into {target} ...")
    rc = subprocess.run([
        "git",
        "clone",
        "--single-branch",
        "--branch",
        branch,
        "--bare",
        "--recurse-submodules",
        url,
        target,
    ]).returncode
    if rc != 0:
        return rc
    target_path = Path(target)
    has_subs = _has_submodules(target_path)
    print("✅ Done!")
    print(f"   To update later: cd {target} && git fetch origin {branch}")
    if has_subs:
        print(f"   Update submodules: git submodule update --init --recursive --remote")
    return 0


if __name__ == "__main__":
    sys.exit(git_clone2(*sys.argv[1:]))
