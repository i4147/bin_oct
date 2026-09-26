#!/data/data/com.termux/files/home/.local/bin/python
"""
Rebase the last N commits interactively (non-interactive squash) in a git repo,
optionally force-pushing afterwards.

Usage:
    python script.py 6
    python script.py 6 --push
    python script.py 6 --backend subprocess --push
    python script.py 6 --backend gitpython
    python script.py 6 --backend dulwich
    python script.py 6 --message "My squashed commit"
    python script.py 6 --dry-run
"""

import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def shell_quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


def git_push() -> None:
    """Force-push the current branch using --force-with-lease (safe force)."""
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    if branch == "HEAD":
        sys.exit("Refusing to push: detached HEAD state.")

    print(f"\nPushing branch '{branch}' with --force-with-lease ...")
    subprocess.run(
        ["git", "push", "--force-with-lease", "origin", branch],
        check=True,
    )
    print("Push complete.")


# ---------------------------------------------------------------------------
# Backend: subprocess (default)
# ---------------------------------------------------------------------------
def rebase_subprocess(n: int, message: str | None, dry_run: bool, push: bool) -> None:
    if not shutil.which("git"):
        sys.exit("git executable not found in PATH")

    log = subprocess.run(
        ["git", "log", f"-{n}", "--pretty=format:%h %s"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    print("Commits to be squashed:")
    print(log)
    print()

    if dry_run:
        print(f"[dry-run] Would run: git rebase -i HEAD~{n}")
        if push:
            print("[dry-run] Would run: git push --force-with-lease origin <branch>")
        return

    editor_src = f"""#!/bin/sh
# Auto-generated sequence editor for squashing {n} commits.
todo="$1"
awk 'NR==1 {{print "pick " $2 " " $3; next}} {{print "squash " $2 " " $3}}' "$todo" > "$todo.new"
mv "$todo.new" "$todo"
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sh") as f:
        f.write(editor_src)
        editor_path = f.name
    os.chmod(editor_path, os.stat(editor_path).st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    env["GIT_SEQUENCE_EDITOR"] = editor_path
    if message:
        env["GIT_EDITOR"] = f"printf '%s\\n' {shell_quote(message)} >"

    try:
        subprocess.run(
            ["git", "rebase", "-i", f"HEAD~{n}"],
            env=env,
            check=True,
        )
    finally:
        try:
            os.unlink(editor_path)
        except OSError:
            pass

    print("\nRebase complete.")

    if push:
        git_push()


# ---------------------------------------------------------------------------
# Backend: GitPython
# ---------------------------------------------------------------------------
def rebase_gitpython(n: int, message: str | None, dry_run: bool, push: bool) -> None:
    try:
        import git
    except ImportError:
        sys.exit("GitPython not installed. Run: pip install GitPython")

    repo = git.Repo(Path.cwd(), search_parent_directories=True)
    commits = list(repo.iter_commits(max_count=n))
    if len(commits) < n:
        sys.exit(f"Only {len(commits)} commits available, cannot rebase {n}.")

    print("Commits to be squashed:")
    for c in commits:
        print(f"{c.hexsha[:7]} {c.summary}")
    print()

    if dry_run:
        print("[dry-run] Would squash the above commits.")
        if push:
            print("[dry-run] Would run: git push --force-with-lease origin <branch>")
        return

    print("Note: GitPython has no native interactive rebase; delegating to git.")
    rebase_subprocess(n, message, dry_run=False, push=push)


# ---------------------------------------------------------------------------
# Backend: Dulwich (pure Python)
# ---------------------------------------------------------------------------
def rebase_dulwich(n: int, message: str | None, dry_run: bool, push: bool) -> None:
    try:
        from dulwich import porcelain
        from dulwich.repo import Repo
    except ImportError:
        sys.exit("dulwich not installed. Run: pip install dulwich")

    repo = Repo.discover(".")
    head = repo.head()
    walker = repo.get_walker(include=[head], max_entries=n)
    commits = [entry.commit for entry in walker]

    if len(commits) < n:
        sys.exit(f"Only {len(commits)} commits available, cannot rebase {n}.")

    print("Commits to be squashed:")
    for c in commits:
        print(f"{c.id.decode()[:7]} {c.message.decode().splitlines()[0]}")
    print()

    if dry_run:
        print("[dry-run] Would squash the above commits.")
        if push:
            print("[dry-run] Would run: git push --force-with-lease origin <branch>")
        return

    oldest = commits[-1]
    if not oldest.parents:
        sys.exit("Cannot squash the root commit with this backend.")

    base = oldest.parents[0]
    tree_id = commits[0].tree
    msg = (message or "Squashed commit").encode()

    new_sha = porcelain.commit(
        repo,
        message=msg,
        author=commits[0].author,
        committer=commits[0].committer,
        tree=tree_id,
        parents=[base],
    )
    repo.refs[b"HEAD"] = new_sha
    print(f"\nRebase complete. New HEAD: {new_sha.decode()[:7]}")

    # Dulwich's push is lower-level; easiest to shell out to git for the push.
    if push:
        git_push()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
BACKENDS = {
    "subprocess": rebase_subprocess,
    "gitpython": rebase_gitpython,
    "dulwich": rebase_dulwich,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Squash the last N commits in the current git repo."
    )
    parser.add_argument("n", type=int, help="number of commits to rebase")
    parser.add_argument(
        "--backend",
        choices=BACKENDS.keys(),
        default="subprocess",
        help="which backend to use (default: subprocess)",
    )
    parser.add_argument(
        "-m",
        "--message",
        default=None,
        help="commit message for the squashed commit",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="force-push with --force-with-lease after rebasing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would happen without doing it",
    )
    args = parser.parse_args()

    if args.n < 1:
        sys.exit("N must be >= 1")

    BACKENDS[args.backend](args.n, args.message, args.dry_run, args.push)


if __name__ == "__main__":
    main()
