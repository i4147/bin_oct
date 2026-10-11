#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that instructs an AI coding agent to write a Python script which auto-commits and pushes the current Git repository. The prompt should describe the purpose, inputs and outputs, dependencies, logic, error handling, edge cases, and usage, without including any code.

Write a Python 3 command-line script named along the lines of an "auto-commit and push" tool for Git repositories. It should be runnable from any directory inside a Git working tree, and it should be intended for use in a Termux environment on Android (the shebang points to Termux's Python at /data/data/com.termux/files/usr/bin/env python), though it must also run on any standard Linux or macOS system with Python 3.

**Dependencies**
- Use only the Python standard library plus the GitPython package (import `Repo`, `GitCommandError`, and `InvalidGitRepositoryError` from `git`). Do not use subprocess-based git calls for the core operations; use GitPython's `Repo` and its `git` interface.
- Use `from __future__ import annotations` at the top, along with `sys`, `datetime`, and `pathlib.Path`.

**Purpose**
The script stages all changes in the current repository, creates a commit with an automatic timestamped message, and pushes the current branch to the remote named `origin`. It is a quick "save and sync" tool.

**Inputs**
- No command-line arguments are required or parsed. The script operates on the repository found by searching from the current working directory `"."` upward through parent directories.
- Implicit inputs: the current working directory, the user's home directory (`~/.gitignore`), the repository's index and HEAD, and the `origin` remote configuration.

**Outputs**
- Errors are printed to standard error with a clear `Error: ...` message prefix.
- On success, print a confirmation to standard output in the form `Pushed to origin/<branch-name>` (the branch name inserted, with a trailing newline).
- Exit with status code 1 on fatal errors; normal completion exits with status 0.

**Required behavior, in order**

1. **Locate the repository.** Create a `Repo` for `"."` with parent-directory searching enabled. If the path is not a git repository (catch `InvalidGitRepositoryError`), print `Error: Not a git repository.` to stderr and exit with status 1. Any other exception during repository access should print `Error accessing repository: <exception message>` to stderr and exit with status 1.

2. **Copy a global gitignore.** Define a helper function `copy_global_gitignore()` that:
   - Looks for `~/.gitignore` (the home directory's file) and a local `.gitignore` in the current directory.
   - If a local `.gitignore` already exists, return immediately without changes.
   - Otherwise, read the home `.gitignore` as UTF-8 and write its contents to a new local `.gitignore` as UTF-8.
   - Silently ignore any exception (missing home file, permission errors, etc.) and return without raising or printing anything. Use a broad `except Exception` so that the failure is swallowed.
   - Call this helper after the repository is successfully opened and before staging.

3. **Stage and commit.** Inside a try block:
   - Stage all changes using the equivalent of `git add -A` via `repo.git.add(A=True)` (this stages additions, modifications, and deletions across the whole repository).
   - Build a timestamp string with `datetime.now()` formatted as `%Y-%m-%d %H:%M:%S`, and create the commit message `Auto-commit at <timestamp>`.
   - Create the commit with `repo.index.commit(message)`. Note that this commits even when there are no staged changes, producing an empty-diff commit; the script does not check for "nothing to commit" unless you deliberately add that guard, so reproduce the behavior as described (commit unconditionally), or document it.

4. **Detached HEAD check.** After committing, if `repo.head.is_detached` is true, print `Error: Could not detect current branch (detached HEAD?).` to stderr and exit with status 1. Note that this check occurs after the commit has been created, so the commit remains on the detached HEAD.

5. **Determine branch and remote.** Get the active branch name from `repo.active_branch.name`. Get the remote named `origin` via `repo.remote("origin")`.

6. **Push.** Call `origin.push(branch)` to push the current branch. Then print `Pushed to origin/<branch>`.

**Error handling and edge cases to reproduce**
- The module imports `GitCommandError`; wrap the staging, commit, and push steps in a try block that catches `GitCommandError` (and/or general exceptions) and reports the failure to stderr with an `Error:` prefix and exits with status 1. Make the error message include the exception text.
- A missing `origin` remote will raise an exception from `repo.remote("origin")`; handle it as a failure with a clear message and exit status 1.
- If the local `.gitignore` already exists, never overwrite it.
- If the home `.gitignore` does not exist, do nothing silently.
- The script must work when launched from a subdirectory of the repository, because it searches parent directories.
- Do not prompt for input; the script must be fully non-interactive.

**Structure**
- Define `copy_global_gitignore()` and `main()`, each with `-> None` type hints.
- Use a standard `if __name__ == "__main__":` guard that calls `main()`.
- Include the Termux shebang line at the top as given.
- Keep the code concise, with clear error messages and no extra features (no logging framework, no configuration files, no argument parsing).

**Usage**
Make the file executable (`chmod +x`) and run it from inside any git repository: `./<script-name>.py`. It requires the GitPython package installed (`pip install GitPython`) and the repository must already have an `origin` remote and the required push credentials configured.
---"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from git import GitCommandError, InvalidGitRepositoryError, Repo


def copy_global_gitignore() -> None:
    home_gitignore = Path.home() / ".gitignore"
    local_gitignore = Path(".gitignore")
    if local_gitignore.exists():
        return
    try:
        data = home_gitignore.read_text(encoding="utf-8")
        local_gitignore.write_text(data, encoding="utf-8")
    except Exception as e:
        return


def main() -> None:
    try:
        repo = Repo(".", search_parent_directories=True)
    except InvalidGitRepositoryError:
        print("Error: Not a git repository.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error accessing repository: {e}", file=sys.stderr)
        sys.exit(1)
    copy_global_gitignore()
    try:
        repo.git.add(A=True)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"Auto-commit at {now}"
        repo.index.commit(commit_msg)
        if repo.head.is_detached:
            print(
                "Error: Could not detect current branch (detached HEAD?).",
                file=sys.stderr,
            )
            sys.exit(1)
        branch = repo.active_branch.name
        origin = repo.remote("origin")
        origin.push(branch)
        print(f"Pushed to origin/{branch} with message: {commit_msg}")
    except GitCommandError as e:
        print(f"Git command error: {e}", file=sys.stderr)
        sys.exit(e.status or 1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
