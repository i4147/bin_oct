#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to recreate a Python script that synchronizes the local master branch of a Git repository with an upstream branch on origin, covering purpose, inputs and outputs, dependencies, logic, error handling, edge cases, and usage. Do not include code or snippets.

Create a single-file Python 3 command-line script (shebang pointing to the Termux Python interpreter at /data/data/com.termux/files/usr/bin/env python) that synchronizes the current local Git branch with an upstream branch fetched from the "origin" remote, using the GitPython library (imported as the `git` package).

Start the script with the `from __future__ import annotations` import, then import `sys` and `Repo` from `git`.

Define one main function, `sync_branch_with_upstream`, that accepts an optional repository path string defaulting to the current directory and returns a boolean indicating success. Wrap the body in a try block for error handling.

Behavior to implement, in order:

1. Open the repository at the given path with `Repo`.
2. Check the active branch name. If it is not "master", print a warning that includes the current branch name, then prompt the user via `input` with the question "Continue anyway? (y/n): ". If the response, lowercased, is not "y", return False immediately.
3. Print "Fetching from origin..." and call fetch on the `origin` remote.
4. Determine the upstream reference: prefer "origin/master" if it exists in the repository's refs; otherwise use "origin/main" if it exists; otherwise print an error stating that neither origin/master nor origin/main exists and return False.
5. Print which upstream branch is being used.
6. Resolve the upstream reference's commit object.
7. Print "Rebasing with unrelated histories..." and record the current active branch object and the current HEAD commit.
8. Run a git rebase through the GitPython `git` interface with the `--onto` option set to the upstream commit, using the recorded HEAD commit as the starting point and the current branch as the branch to rebase, passing the `allow_unrelated_histories=True` keyword so unrelated histories are permitted. The inner rebase call must be guarded by its own try/except so that a rebase failure can be handled separately from other errors (for example, by reporting the failure and aborting or restoring the original state, and returning False).

Outer error handling: catch any other exception raised during the overall process, print a descriptive error message including the exception text, and return False.

Implement a standard entry point guard so the script runs when executed directly. Pass the first command-line argument (if provided, from `sys.argv`) as the repository path, defaulting to the current directory. Exit with status 0 if the function returns True, and exit with status 1 otherwise.

Notable details and edge cases to handle:
- The script is interactive when not on master; it blocks on user input.
- Only the "origin" remote is used; its absence will raise an error caught by the outer handler.
- Both master and main are supported as upstream, with master taking precedence.
- The rebase uses unrelated-history permission, so it can combine histories that share no common ancestor.
- Output is plain text printed to standard output; warnings and errors are printed with "Warning:" and "Error:" prefixes.
- Keep the code concise, idiomatic, and consistent in style, using f-strings for formatted messages, and add no features beyond those described.
---"""

from __future__ import annotations

import sys

from git import Repo


def sync_branch_with_upstream(repo_path: str = ".") -> bool:
    try:
        repo = Repo(repo_path)
        if repo.active_branch.name != "master":
            print(
                "Warning: Not on master branch. Current branch:",
                repo.active_branch.name,
            )
            response = input("Continue anyway? (y/n): ")
            if response.lower() != "y":
                return False
        print("Fetching from origin...")
        origin = repo.remotes.origin
        origin.fetch()
        upstream_branch = None
        if "origin/master" in repo.refs:
            upstream_branch = "origin/master"
        elif "origin/main" in repo.refs:
            upstream_branch = "origin/main"
        else:
            print("Error: Neither origin/master nor origin/main exists")
            return False
        print(f"Using upstream branch: {upstream_branch}")
        upstream_commit = repo.refs[upstream_branch].commit
        print("Rebasing with unrelated histories...")
        current_branch = repo.active_branch
        original_head = repo.head.commit
        try:
            repo.git.rebase(
                "--onto",
                upstream_commit,
                original_head,
                current_branch,
                allow_unrelated_histories=True,
            )
            print("Rebase successful")
        except Exception as e:
            print(f"Rebase failed: {e}")
            repo.git.rebase("--abort")
            return False
        print(f"Pushing to origin/{current_branch.name} with force-with-lease...")
        origin.push(
            refspec=f"{current_branch.name}:{current_branch.name}",
            force_with_lease=True,
        )
        print("Successfully synced branch!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def sync_with_plumbing(repo_path: str = ".") -> bool:
    try:
        repo = Repo(repo_path)
        origin = repo.remotes.origin
        origin.fetch()
        upstream_ref = None
        for ref in repo.refs:
            if ref.name in ["origin/master", "origin/main"]:
                upstream_ref = ref
                break
        if not upstream_ref:
            print("No origin/master or origin/main found")
            return False
        current_commit = repo.head.commit
        upstream_commit = upstream_ref.commit
        if current_commit != upstream_commit:
            print(f"Rebasing {current_commit.hexsha[:8]} onto {upstream_commit.hexsha[:8]}")
            temp_branch = repo.create_head("temp_rebase", current_commit)
            temp_branch.checkout()
            try:
                repo.head.reset(upstream_commit, index=True, working_tree=True)
                repo.git.cherry_pick(f"{current_commit.hexsha}..{upstream_commit.hexsha}")
                repo.git.cherry_pick("--continue")
                repo.head.reference = repo.head.commit
            except Exception as e:
                print(f"Rebase failed: {e}")
                repo.git.rebase("--abort")
                return False
            finally:
                if temp_branch in repo.branches:
                    repo.delete_head(temp_branch)
        origin.push(refspec="master:master", force_with_lease=True)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = sync_branch_with_upstream(".")
    sys.exit(0 if success else 1)
