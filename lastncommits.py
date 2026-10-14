#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that inspects the recent history of a local Git repository and reports the files that were newly added within the last N commits. The script should accept the number of commits to examine as a command-line argument, and it should print the resulting list of added file paths to standard output, one per line, so the output is easy to read or pipe into other tools.
Key behaviors to implement:
- Require the commit count as a positional argument. If it is missing, display a brief usage message explaining how to run the script and exit with a non-zero status.
- Query the repository's commit history for only the most recent N commits, considering only changes where a file was created (not modified, renamed, or deleted).
- Skip any entries that are symbolic links, so that only regular files are reported.
- Return the paths as path objects or normalized strings, preserving the order in which Git reports them.
- If the Git command fails (for example, when the current directory is not a repository or Git is not installed), print a clear error message to standard error, including Git's own error output when available, and exit with a non-zero status.
- Handle unexpected exceptions gracefully by printing a concise error message to standard error and exiting with a non-zero status rather than displaying a raw traceback.
- Use a clean, well-structured layout with a clear separation between data retrieval and command-line handling, and include a `main` entry point that runs only when the script is executed directly.
- Use clear status symbols or prefixes in error messages to make failures easy to spot, and keep normal output limited to the file list alone.
---"""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys


def get_created_files(n_commits: int) -> list:
    try:
        cmd = [
            "git",
            "log",
            "-n",
            str(n_commits),
            "--pretty=format:",
            "--name-status",
            "--diff-filter=A",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        created_files = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split("\t")
                if len(parts) >= 2:
                    path = parts[1]
                    path = Path(path)
                    if path.is_symlink():
                        continue
                    created_files.append(path)
        return created_files
    except subprocess.CalledProcessError as e:
        print(f"✗ Git command failed: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 list_commits.py <N>")
        print("       where N is the number of commits to analyze")
        print("\nExamples:")
        print("  python3 list_commits.py 5")
        print("  python3 list_commits.py 10")
        sys.exit(1)
    try:
        n_commits = int(sys.argv[1])
        if n_commits <= 0:
            print("✗ Error: Number of commits must be positive", file=sys.stderr)
            sys.exit(1)
        created_files = get_created_files(n_commits)
        if created_files:
            for path in created_files:
                print(path)
        else:
            print(
                f"No files created in the last {n_commits} commit(s)",
                file=sys.stderr,
            )
    except ValueError:
        print(f"✗ Error: '{sys.argv[1]}' is not a valid integer", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
