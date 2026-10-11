#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with the following specification:

Create a standalone Python 3 command-line script, intended to run under Termux on Android (use a Termux-style shebang pointing to the Termux Python interpreter at /data/data/com.termux/files/usr/bin/env python). Begin the file with the shebang line, then `from __future__ import annotations`. Use only the standard library: `subprocess` and `pathlib`. Do not use any third-party packages.

Purpose: The script recursively discovers every Git repository beneath the directory it is launched from and runs a fast-forward-only pull in each one. It is meant to update a whole tree of cloned projects in one command.

Behavior to implement:

1. Starting directory: the current working directory at launch time, resolved via the path library's current-directory method.
2. Repository detection: a directory counts as a Git repository if it contains a `.git` subdirectory (check that it is a directory, not merely that the entry exists). Do not inspect the contents of `.git` further.
3. Pulling: for each detected repository, print a blank line followed by an arrow-style header naming the repository's full path (format: a newline, then `==> Pulling in repo: <path>`). Then run `git -C <repo path> pull --ff-only` through the subprocess module with `check=True`. Pass arguments as a list, never through a shell. Let git's own output stream to the terminal (do not capture it).
4. Failure handling for pulls: catch the subprocess error raised when git exits nonzero, and print a warning line beginning with a warning emoji and two spaces, reading `git pull failed in: <path>`. Do not abort; continue with the remaining repositories. If git itself is not installed, the resulting not-found error is not specifically required to be handled, but the script must not crash silently for the normal nonzero-exit case.
5. Recursion rules: when a directory is not itself a Git repository, iterate over its immediate children. Recurse only into children that are directories and whose name is not exactly `.git`. Once a directory is identified as a repository, do not descend further into it, so nested repositories inside a repository are skipped. Symbolic links to directories are followed the same way as ordinary directories (use the standard directory check on the path).
6. Permission handling: wrap each directory listing in a try block that catches permission errors and silently skips that directory without printing anything.
7. Main flow: the main function determines the root, walks and pulls starting there, then prints a blank line followed by `Done.`. Return nothing.
8. Entry point: guard execution with the standard `if __name__ == "__main__":` check and invoke main via `raise SystemExit(main())`, so the exit status follows what main returns (None results in exit status zero).
9. Type hints: annotate all functions with parameter and return types, using `Path` for paths and `None` for functions that return nothing. Use the same helper decomposition: one function to detect a repository, one to pull a repository, one to walk recursively, and one main.
10. Style: keep the code short and plain, with no classes, no logging framework, no argument parsing, no configuration files, and no extra output beyond what is described. Use f-strings for printed messages.

Expected output on the terminal: for each repository found, a header line and git's own pull output; a warning line for any failed pull; and a final `Done.` line. The script makes no changes other than what git pull performs in each repository, and it never runs git on directories that are not repositories.

Deliver the complete script as a single file.
---"""

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
