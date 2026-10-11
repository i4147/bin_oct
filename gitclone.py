#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that asks an AI coding agent to recreate a Python script which shallow-clones a Git repository's default branch along with its submodules. The prompt should be detailed enough for the agent to reproduce the script from scratch, but must not include code or code snippets.

Create a single-file Python 3 script (intended for Termux on Android, so use a `#!/data/data/com.termux/files/usr/bin/env python` shebang and `from __future__ import annotations`) that acts as a "git clone with default branch only" helper, invoked as a command named `g2`.

**Purpose:** Clone a Git repository containing only its remote default branch (not all branches), including its submodules, into a target directory.

**Inputs:**
- Positional argument 1: repository URL (required).
- Positional argument 2: target directory (optional). If omitted, the target is the repository name derived from the URL (last path component, trailing slashes stripped, and a `.git` suffix removed), with `.git` appended, e.g. `<name>.git`.
- No arguments: print the usage line `Usage: g2 <repo-url> [target-dir]` and return exit code 1.

**Outputs:**
- Progress messages printed to stdout, using these exact formats with emoji:
  - `🔍 Default branch: <branch>`
  - `📦 Cloning only '<branch>' (with submodules) from <url> into <target> ...`
- Error message printed to stderr on failure to detect the branch: `❌ Could not determine default branch for <url>`.
- The function returns an integer exit status, which the script's entry point passes to `sys.exit`.

**Key logic and helpers:**
1. `_default_branch(url)`: run `git ls-remote --symref <url> HEAD` via `subprocess.run` with `capture_output=True, text=True`. If the return code is nonzero, return `None`. Otherwise scan stdout lines with a regex matching `ref: refs/heads/<branch> HEAD` and return the branch name, or `None` if no match.
2. `_has_submodules(repo_dir)`: run `git -C <repo_dir> cat-file -e HEAD:.gitmodules` with captured output and return `True` only if the return code is 0. (Helper available for checking whether a cloned repo has submodules.)
3. `git_clone2(*args)`:
   - Validate args as described above.
   - Detect the default branch; on failure print the error to stderr and return 1.
   - Derive the repo name and default target as described.
   - Print the two progress messages.
   - Run `git clone` with `--single-branch`, `--branch <branch>`, `--depth 1` (shallow), and `--recurse-submodules` plus a shallow submodule option such as `--shallow-submodules`, followed by the URL and target directory, using `subprocess.run` as a list (no shell). Return the clone's return code. Print a success or failure message depending on the outcome (e.g., a checkmark message on success, a cross message on failure) and return the status code accordingly.
4. Entry point: when run as `__main__`, call `git_clone2` with `sys.argv[1:]` and exit with its return value.

**Dependencies:** Python standard library only (`re`, `subprocess`, `sys`, `pathlib`). Requires the `git` executable on PATH.

**Edge cases and behavior notes:**
- Trailing slashes and `.git` suffixes in URLs must be handled when deriving the directory name.
- If the remote's HEAD is detached or has no symbolic ref, the branch cannot be determined and the script fails.
- Git errors during clone are surfaced through the process return code; the script should not swallow them.
- Use list-form subprocess calls to avoid shell injection; do not use `shell=True`.
- Keep the script concise, with type hints where natural, and match the terse style of the description above.

Deliver the complete script as a single file named `g2.py`, with the shebang line first.
---"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


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
