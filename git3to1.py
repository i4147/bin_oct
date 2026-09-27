#!/data/data/com.termux/files/home/.local/bin/python
"""Squash the last N commits into one and set the commit date to today.

Usage:
    python squash_commits.py [--count 3] [--date "2026-09-27 14:30:00"]
    python squash_commits.py -c 3 -d "today"

Requires:
    - git installed and available in PATH
    - You must be inside a git repository
    - The last N commits must not have been pushed yet (or you accept
      force-pushing to overwrite remote history)
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=check,
    )
    return result


def get_commit_count() -> int:
    result = run_git(["rev-list", "--count", "HEAD"])
    return int(result.stdout.strip())


def get_commit_message(commit: str) -> str:
    result = run_git(["log", "-1", "--format=%B", commit])
    return result.stdout


def squash_commits(count: int, commit_date: str | None = None) -> bool:
    if count < 2:
        print(f"Error: Need at least 2 commits to squash, got {count}", file=sys.stderr)
        return False

    try:
        run_git(["rev-parse", "--git-dir"])
    except subprocess.CalledProcessError:
        print("Error: Not inside a git repository", file=sys.stderr)
        return False

    total_commits = get_commit_count()
    if count > total_commits:
        print(
            f"Error: Only {total_commits} commit(s) available, cannot squash {count}",
            file=sys.stderr,
        )
        return False

    first_commit = run_git(["rev-parse", f"HEAD~{count - 1}"]).stdout.strip()
    commit_message = get_commit_message(first_commit)

    todo_lines = []
    for i in range(count):
        commit_sha = run_git(["rev-parse", f"HEAD~{count - 1 - i}"]).stdout.strip()
        subject = run_git(["log", "-1", "--format=%s", commit_sha]).stdout.strip()
        action = "pick" if i == 0 else "squash"
        todo_lines.append(f"{action} {commit_sha} {subject}")

    todo_text = "\n".join(todo_lines) + "\n"

    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        editor_script = f"""
#!/bin/sh
cat > "\$1" << 'EOF'
{todo_text}
EOF
"""
        f.write(editor_script)
        editor_path = f.name

    try:
        Path(editor_path).chmod(0o755)

        env = {"GIT_SEQUENCE_EDITOR": editor_path}
        result = subprocess.run(
            ["git", "rebase", "-i", f"HEAD~{count}"],
            capture_output=True,
            text=True,
            env={**__import__("os").environ, **env},
        )

        if result.returncode != 0:
            print(f"Rebase failed: {result.stderr}", file=sys.stderr)

            run_git(["rebase", "--abort"], check=False)
            return False

    finally:
        Path(editor_path).unlink(missing_ok=True)

    if commit_date is None:
        date_str = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    else:
        try:
            parsed = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
            date_str = parsed.strftime("%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            date_str = commit_date

    amend_result = run_git(
        ["commit", "--amend", "--no-edit", "--date", date_str],
        check=False,
    )
    if amend_result.returncode != 0:
        print(f"Failed to amend commit date: {amend_result.stderr}", file=sys.stderr)
        return False

    print(f"Successfully squashed {count} commits into one.")
    print(f"Commit date set to: {date_str}")
    print("\nTo push to remote, run:")
    print("  git push --force-with-lease")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Squash the last N commits into one and set the date.",
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=3,
        help="Number of commits to squash (default: 3)",
    )
    parser.add_argument(
        "-d",
        "--date",
        default=None,
        help=(
            'Commit date. Use "today" for current date, or an ISO format '
            'string like "2026-09-27 14:30:00". Default: current date/time.'
        ),
    )
    args = parser.parse_args()

    if args.date and args.date.lower() == "today":
        args.date = None

    success = squash_commits(args.count, args.date)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
