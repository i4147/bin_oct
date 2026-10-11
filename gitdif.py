#!/data/data/com.termux/files/usr/bin/env python
"""I'm going to write the prompt now.

Write a self-contained prompt that instructs an AI coding agent to build a Python 3 command-line script that scans a set of directories for Git repositories and reports which of them have uncommitted changes. Follow the specification below exactly; do not include source code or code snippets in your output.

**Purpose:** The script checks the working-tree status of multiple local Git repositories in parallel and prints a concise report, so the user can see at a glance which repositories have uncommitted or untracked work.

**Target environment:** The script runs under Termux on Android. Its shebang line points to the Termux Python interpreter path (`/data/data/com.termux/files/usr/bin/env python`). Use only the Python standard library. Use the `from __future__ import annotations` import so modern type hints (such as `X | None` and `tuple[...]`) work.

**Dependencies:** Standard library only: `subprocess`, `sys`, `multiprocessing` (`Pool`, `cpu_count`), and `pathlib.Path`. The script requires the `git` executable to be available on the system PATH.

**Per-repository check (a worker function):**
- Accept a `Path` to a repository directory and return a tuple of `(repo_path, has_changes: bool, message: str | None)`.
- First verify that `<repo_path>/.git` exists and is a directory. If not, return `(repo_path, False, "Not a git repository")`.
- Otherwise run `git status --porcelain` with the repository as the working directory, capturing stdout and stderr as text, with a timeout of 5 seconds.
- If the command exits with a non-zero return code, return `(repo_path, False, "Git error: <stderr stripped>")`.
- If stdout is non-empty (after stripping), it indicates changes. Split the output by newlines. For each line, take the first two characters as the status code and the text from index 3 onward as the file path. Skip entries whose status code is blank after stripping whitespace. Format each entry as `"<status> <file>"`.
- Join at most the first 5 entries with `", "`. If there are more than 5 entries, append `" (+N more)"` where N is the remaining count. Return `(repo_path, True, summary)`.
- If stdout is empty, return `(repo_path, False, "Clean")`.
- Catch `subprocess.TimeoutExpired` and return `(repo_path, False, "Timeout checking git status")`.
- Catch any other exception and return `(repo_path, False, "<error message>")` using the exception's string form, so one failing repository never crashes the whole run.

**Main program flow:**
- Determine the list of repository paths to scan from the command-line arguments (directories passed as arguments). Each argument is a path to a repository; convert each to a `Path`. Provide sensible handling if no arguments are given (print a short usage message to stderr and exit with a non-zero status), and decide whether to also accept a parent directory and scan its immediate subdirectories — document the chosen behavior in a usage string.
- Run the worker across all repositories in parallel using `multiprocessing.Pool` sized to `cpu_count()`, using `pool.map` (or equivalent) so results are returned in input order.
- Print a report: a header line, then one line per repository showing a marker (for example a checkmark or a clear symbol for clean, and a warning symbol for changes or errors), the repository's name (directory name), and the message. Make the output readable in a plain terminal.
- At the end, print a summary line with counts of repositories with changes, clean repositories, and non-repositories or errors.
- Exit with status 0 when all repositories are clean, and a non-zero status (e.g., 1) when any repository has uncommitted changes, so the script is usable in shell scripts. Print nothing extra to stdout beyond the report.

**Execution details:**
- Guard the entry point with `if __name__ == "__main__":` so multiprocessing works correctly (required for spawn-based start methods).
- Make the script executable with the Termux shebang line at the top.

**Edge cases to handle:**
- A path that does not exist or is not a directory: treat as "Not a git repository" (the `.git` check covers this) without crashing.
- Repositories with a `.git` file instead of directory (e.g., worktrees/submodules): the spec treats these as not a repository; mention this as a known limitation in a code comment.
- Very long file lists: truncate to 5 entries as described.
- Paths with spaces: pass the path as a `Path` object, not a shell string.
- Command output with trailing whitespace or blank lines: strip before splitting.

**Style:** Keep the code short, typed with the same annotations as described, use concise docstrings or comments only where helpful, and avoid external libraries.
---"""

from __future__ import annotations

import subprocess
import sys
from multiprocessing import Pool, cpu_count
from pathlib import Path


def get_repo_status(repo_path: Path) -> tuple[Path, bool, str | None]:
    try:
        git_dir = repo_path / ".git"
        if not git_dir.exists() or not git_dir.is_dir():
            return (repo_path, False, "Not a git repository")
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return (repo_path, False, f"Git error: {result.stderr.strip()}")
        has_changes = bool(result.stdout.strip())
        if has_changes:
            lines = result.stdout.strip().split("\n")
            changes = []
            for line in lines:
                status = line[:2]
                file = line[3:]
                if status.strip():
                    changes.append(f"{status} {file}")
            change_summary = ", ".join(changes[:5])
            if len(changes) > 5:
                change_summary += f" (+{len(changes) - 5} more)"
            return (repo_path, True, change_summary)
        else:
            return (repo_path, False, "Clean")
    except subprocess.TimeoutExpired:
        return (repo_path, False, "Timeout checking git status")
    except Exception as e:
        return (repo_path, False, f"Error: {e!s}")


def find_git_repos(directory: Path) -> list[Path]:
    repos = []
    for item in directory.iterdir():
        if item.is_dir() and not item.name.startswith(".") and (item / ".git").is_dir():
            repos.append(item)
    return repos


def print_result(result: tuple[Path, bool, str | None]) -> None:
    path, has_changes, info = result
    if not has_changes:
        print(f"✓ {path.name}: No changes")
        if info and info != "Clean":
            print(f"  └─ {info}")
    else:
        print(f"✗ {path.name}: CHANGES DETECTED")
        if info:
            print(f"  └─ {info}")


def main():
    root_dir = Path.cwd()
    print(f"Scanning for git repositories in: {root_dir}\n")
    repos = find_git_repos(root_dir)
    if not repos:
        print("No git repositories found in current directory.")
        return
    print(f"Found {len(repos)} git repository(ies)\n")
    num_processes = min(cpu_count(), len(repos), 8)
    print(f"Checking repositories using {num_processes} process(es)...\n")
    with Pool(processes=num_processes) as pool:
        results = pool.map(get_repo_status, repos)
    changed_count = sum(1 for _, has_changes, _ in results if has_changes)
    if changed_count > 0:
        print("=" * 40)
        print(f"⚠️  Found {changed_count} repository(ies) with changes")
        print("=" * 40)
    else:
        print("=" * 40)
        print("✅ All repositories are clean")
        print("=" * 40)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
