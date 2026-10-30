#!/data/data/com.termux/files/usr/bin/env python
"""Report added and removed paths for every reachable Git commit."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Sequence


class GitError(RuntimeError):
    """Raised when a Git command cannot be completed."""


@dataclass
class CommitInfo:
    commit_hash: str
    parents: list[str]
    date: str
    subject: str


@dataclass
class CommitReport:
    hash: str
    date: str
    subject: str
    added: list[str]
    removed: list[str]


def run_git(cwd: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise GitError(f"Could not run Git: {exc}") from exc

    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        command = " ".join(["git", *args])
        raise GitError(f"{command} failed: {detail or 'unknown Git error'}")

    return result.stdout


def find_repository(path: Path) -> Path:
    """Resolve a supplied directory to the repository root using pathlib."""
    candidate = path.expanduser().resolve()
    if not candidate.is_dir():
        raise GitError(f"Not a directory: {candidate}")

    is_bare = run_git(candidate, "rev-parse", "--is-bare-repository").strip() == b"true"
    if is_bare:
        return candidate

    root = os.fsdecode(run_git(candidate, "rev-parse", "--show-toplevel").rstrip(b"\n"))
    return Path(root).expanduser().resolve()


def read_commits(repo: Path) -> list[CommitInfo]:
    # --all includes every ref; adding HEAD also covers detached checkouts.
    revisions = ["--all"]
    try:
        run_git(repo, "rev-parse", "--verify", "--quiet", "HEAD")
    except GitError:
        pass
    else:
        revisions.append("HEAD")

    output = run_git(
        repo,
        "log",
        *revisions,
        "--reverse",
        "--topo-order",
        "--format=tformat:%H%x00%P%x00%cs%x00%s",
    )

    commits: list[CommitInfo] = []
    for record in output.split(b"\n"):
        if not record:
            continue
        fields = record.split(b"\x00", 3)
        if len(fields) != 4:
            raise GitError("Could not parse Git commit metadata.")

        commits.append(
            CommitInfo(
                commit_hash=fields[0].decode("ascii"),
                parents=fields[1].decode("ascii").split(),
                date=fields[2].decode("ascii"),
                subject=fields[3].decode("utf-8", errors="replace"),
            )
        )
    return commits


def read_added_and_removed(repo: Path, commit: CommitInfo) -> tuple[list[str], list[str]]:
    # Compare merge commits with their first parent, matching normal git log history.
    if commit.parents:
        output = run_git(
            repo,
            "diff",
            "--no-renames",
            "--name-status",
            "--diff-filter=AD",
            "-z",
            commit.parents[0],
            commit.commit_hash,
        )
    else:
        # A root commit is compared with Git's empty tree.
        output = run_git(
            repo,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-status",
            "-r",
            "--no-renames",
            "--diff-filter=AD",
            "-z",
            commit.commit_hash,
        )

    fields = output.split(b"\x00")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 2:
        raise GitError(f"Could not parse changed paths for {commit.commit_hash}.")

    added: list[str] = []
    removed: list[str] = []
    for index in range(0, len(fields), 2):
        status, raw_path = fields[index], fields[index + 1]
        path = PurePosixPath(os.fsdecode(raw_path)).as_posix()
        if status == b"A":
            added.append(path)
        elif status == b"D":
            removed.append(path)

    return sorted(added), sorted(removed)


def build_report(repo: Path) -> list[CommitReport]:
    reports: list[CommitReport] = []
    for commit in read_commits(repo):
        added, removed = read_added_and_removed(repo, commit)
        reports.append(
            CommitReport(
                hash=commit.commit_hash,
                date=commit.date,
                subject=commit.subject,
                added=added,
                removed=removed,
            )
        )
    return reports


def print_text(repo: Path, reports: list[CommitReport]) -> None:
    print(f"Repository: {repo}")
    if not reports:
        print("No commits found.")
        return

    for report in reports:
        print(f"\n{report.hash[:12]}  {report.date}  {report.subject or '(no subject)'}")
        for label, paths in (("Added", report.added), ("Removed", report.removed)):
            print(f"  {label}:")
            if paths:
                for path in paths:
                    print(f"    {path}")
            else:
                print("    (none)")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List only added and removed paths for each reachable commit.",
        epilog=(
            "All refs and HEAD are included. Renames are shown as a removed old path and an added new path; "
            "merge commits are compared with their first parent."
        ),
    )
    parser.add_argument(
        "repo",
        nargs="?",
        type=Path,
        default=Path("."),
        help="repository directory (defaults to the current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="write a JSON report, including commits with no added or removed paths",
    )
    args = parser.parse_args(argv)

    try:
        repo = find_repository(args.repo)
        reports = build_report(repo)
    except GitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json_output:
        payload = {"repository": str(repo), "commits": [asdict(report) for report in reports]}
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=True)
        sys.stdout.write("\n")
    else:
        print_text(repo, reports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
