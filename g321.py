#!/data/data/com.termux/files/home/.local/bin/python
"""Squash the last N git commits into one, then force-push. Full auto.

Reads GITHUB_TOKEN from ~/.env (if present) and uses it for the push,
without ever writing it to disk or to ~/.gitconfig.

Usage:
    python script.py                # squash last 3, push
    python script.py 6              # squash last 6
    python script.py 6 -b gitpython # use GitPython for reads
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# ===========================================================================
# Environment loading
# ===========================================================================


def _load_env_file(path: Path | None = None) -> None:
    """Populate os.environ from ~/.env if the keys aren't already set.

    Accepts lines of the form:
        KEY=value
        KEY="value"
        KEY='value'
        export KEY=value

    Blank lines and lines starting with '#' are ignored. Values already
    present in the real environment are NOT overwritten (setdefault),
    so an explicit `GITHUB_TOKEN=... python script.py` on the command
    line always wins over ~/.env.
    """
    path = path or (Path.home() / ".env")
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        # Strip optional "export " prefix.
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, val)


# ===========================================================================
# Backends
# ===========================================================================


class SubprocessBackend:
    """Default backend. Shells out to the ``git`` executable for everything.

    Every other backend inherits from this class. Methods it doesn't
    override therefore keep using subprocess, which is exactly the
    "fallback to subprocess if needed" contract.
    """

    name = "subprocess"

    def __init__(self) -> None:
        pass

    # -- low-level runner --------------------------------------------------

    def _run(
        self,
        args: list[str],
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=check,
            env=env,
        )

    # -- read operations ---------------------------------------------------

    def is_repo(self) -> bool:
        try:
            self._run(["rev-parse", "--git-dir"])
            return True
        except subprocess.CalledProcessError:
            return False

    def count_commits(self) -> int:
        return int(self._run(["rev-list", "--count", "HEAD"]).stdout.strip())

    def rev_parse(self, ref: str) -> str:
        return self._run(["rev-parse", ref]).stdout.strip()

    def commit_subject(self, commit: str) -> str:
        return self._run(["log", "-1", "--format=%s", commit]).stdout.strip()

    def commit_message(self, commit: str) -> str:
        return self._run(["log", "-1", "--format=%B", commit]).stdout

    # -- write operations --------------------------------------------------

    def rebase_interactive(self, count: int, todo_content: str) -> tuple[bool, str]:
        """Run ``git rebase -i HEAD~count`` with a pre-baked todo list.

        Git invokes ``$GIT_SEQUENCE_EDITOR <todo-file>`` once. We point it
        at a tiny Python script that overwrites the todo file. This avoids
        the shell heredoc / ``$1`` / ``\\$1`` trap entirely.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(
                "import pathlib, sys\n"
                f"pathlib.Path(sys.argv[1]).write_text("
                f"{todo_content!r}, encoding='utf-8')\n"
            )
            editor_path = fh.name
        try:
            env = {
                **os.environ,
                "GIT_SEQUENCE_EDITOR": (
                    f"{shlex.quote(sys.executable)} {shlex.quote(editor_path)}"
                ),
            }
            result = subprocess.run(
                ["git", "rebase", "-i", f"HEAD~{count}"],
                capture_output=True,
                text=True,
                env=env,
            )
            if result.returncode != 0:
                return False, result.stderr
            return True, ""
        finally:
            Path(editor_path).unlink(missing_ok=True)

    def amend_date(self, date_str: str) -> tuple[bool, str]:
        # --date takes the date as its own argument; no `-m` in between.
        result = self._run(
            ["commit", "--amend", "--no-edit", "--date", date_str],
            check=False,
        )
        return result.returncode == 0, result.stderr

    def push_force_with_lease(self) -> tuple[bool, str]:
        """Push with --force-with-lease, using GITHUB_TOKEN if available.

        The token is injected via a one-shot `-c url.<token>@github.com/
        .insteadOf=https://github.com/` override. It lives only in this
        subprocess's argv — never written to ~/.gitconfig, never to disk.

        GIT_TERMINAL_PROMPT=0 makes git fail fast instead of hanging if
        the token is missing or invalid.
        """
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        cmd: list[str] = ["git"]

        token = os.environ.get("GITHUB_TOKEN")
        if token:
            cmd += [
                "-c",
                f"url.https://x-access-token:{token}@github.com/.insteadOf="
                f"https://github.com/",
            ]

        cmd += ["push", "--force-with-lease"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

        stderr = result.stderr
        if token:
            # Scrub the token from any error output git might echo back.
            stderr = stderr.replace(token, "***")
        return result.returncode == 0, stderr

    def abort_rebase(self) -> None:
        try:
            self._run(["rebase", "--abort"], check=False)
        except Exception:
            pass


# --- GitPython ------------------------------------------------------------


class GitPythonBackend(SubprocessBackend):
    """Uses GitPython for read operations. Rebase / amend / push still
    go through subprocess because GitPython has no clean interactive
    rebase API.
    """

    name = "gitpython"

    def __init__(self) -> None:
        try:
            import git  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("gitpython not installed") from exc
        self._git = git
        self._repo = git.Repo(os.getcwd(), search_parent_directories=True)

    def is_repo(self) -> bool:
        return True  # constructor would have raised otherwise

    def count_commits(self) -> int:
        return sum(1 for _ in self._repo.iter_commits("HEAD"))

    def rev_parse(self, ref: str) -> str:
        return self._repo.commit(ref).hexsha

    def commit_subject(self, commit: str) -> str:
        return self._repo.commit(commit).summary

    def commit_message(self, commit: str) -> str:
        return self._repo.commit(commit).message


# --- libgit2 (pygit2) -----------------------------------------------------


class Libgit2Backend(SubprocessBackend):
    """Uses pygit2 (libgit2 bindings) for read operations. libgit2 has no
    interactive rebase, so writes fall back to subprocess.
    """

    name = "libgit2"

    def __init__(self) -> None:
        try:
            import pygit2  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("pygit2 (libgit2 bindings) not installed") from exc
        discovered = pygit2.discover_repository(os.getcwd())
        if not discovered:
            raise RuntimeError("not inside a git repository")
        self._pygit2 = pygit2
        self._repo = pygit2.Repository(discovered)

    def is_repo(self) -> bool:
        return True

    def count_commits(self) -> int:
        return sum(1 for _ in self._repo.walk(self._repo.head.target))

    def rev_parse(self, ref: str) -> str:
        return str(self._repo.revparse_single(ref).id)

    def commit_subject(self, commit: str) -> str:
        c = self._repo.revparse_single(commit)
        return c.message.split("\n", 1)[0]

    def commit_message(self, commit: str) -> str:
        c = self._repo.revparse_single(commit)
        return c.message


# --- dulwich --------------------------------------------------------------


class DulwichBackend(SubprocessBackend):
    """Pure-Python git via dulwich. Read ops native; writes fall back."""

    name = "dulwich"

    def __init__(self) -> None:
        try:
            from dulwich.repo import Repo  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("dulwich not installed") from exc
        self._Repo = Repo
        self._repo = Repo.discover(os.getcwd())

    def is_repo(self) -> bool:
        return True

    def count_commits(self) -> int:
        return sum(1 for _ in self._repo.get_walker())

    def rev_parse(self, ref: str) -> str:
        return self._repo[ref.encode()].id.decode()

    def commit_subject(self, commit: str) -> str:
        c = self._repo[commit.encode()]
        return c.message.decode(errors="replace").split("\n", 1)[0]

    def commit_message(self, commit: str) -> str:
        c = self._repo[commit.encode()]
        return c.message.decode(errors="replace")


# --- PyGithub (remote-only) ----------------------------------------------


class PyGithubBackend(SubprocessBackend):
    """PyGithub talks to GitHub's remote API only; it cannot perform local
    rebase or amend. Every operation therefore falls back to subprocess.
    """

    name = "pygithub"

    def __init__(self) -> None:
        try:
            import github  # type: ignore[import-not-found]  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("PyGithub not installed") from exc
        # Remote-API-only; falls back to subprocess silently.


# --- registry & factory ---------------------------------------------------


_BACKEND_REGISTRY: dict[str, type[SubprocessBackend]] = {
    "subprocess": SubprocessBackend,
    "gitpython": GitPythonBackend,
    "libgit2": Libgit2Backend,
    "dulwich": DulwichBackend,
    "pygithub": PyGithubBackend,
}


def build_backend(name: str) -> SubprocessBackend:
    """Instantiate the requested backend, falling back to subprocess on
    any failure (unknown name, missing library, not a repo, etc.).
    """
    norm = name.lower()

    if norm == "subprocess":
        return SubprocessBackend()

    # Not-a-backend / typo handling.
    if norm == "typer":
        norm = "subprocess"
    if norm == "dulwitch":
        norm = "dulwich"

    cls = _BACKEND_REGISTRY.get(norm)
    if cls is None:
        return SubprocessBackend()

    try:
        return cls()
    except Exception as exc:
        print(
            f"warning: backend {name!r} unavailable ({exc}); using subprocess.",
            file=sys.stderr,
        )
        return SubprocessBackend()


# ===========================================================================
# Core operation
# ===========================================================================


def squash_commits(backend: SubprocessBackend, count: int) -> bool:
    """Squash the last ``count`` commits into one, stamp with "now",
    and force-push. Returns True on success, False on any handled failure.
    """
    if count < 2:
        print(
            f"error: need at least 2 commits to squash, got {count}",
            file=sys.stderr,
        )
        return False

    if not backend.is_repo():
        print("error: not inside a git repository", file=sys.stderr)
        return False

    total = backend.count_commits()
    if count > total:
        print(
            f"error: only {total} commit(s) available, cannot squash {count}",
            file=sys.stderr,
        )
        return False

    # Build the interactive rebase todo list, oldest -> newest.
    # First line is `pick`, every following line is `squash`.
    todo: list[str] = []
    for i in range(count):
        h = backend.rev_parse(f"HEAD~{count - 1 - i}")
        subject = backend.commit_subject(h)
        action = "pick" if i == 0 else "squash"
        todo.append(f"{action} {h} {subject}")
    todo_content = "\n".join(todo) + "\n"

    ok, err = backend.rebase_interactive(count, todo_content)
    if not ok:
        print(f"error: rebase failed: {err}", file=sys.stderr)
        backend.abort_rebase()
        return False

    # Stamp the squashed commit's author date with "now" (UTC).
    formatted = datetime.now(timezone.utc).strftime("%a,%d%b%Y%H:%M:%S%z")
    ok, err = backend.amend_date(formatted)
    if not ok:
        print(f"error: failed to amend commit date: {err}", file=sys.stderr)
        return False

    # Force-push with lease (uses GITHUB_TOKEN if present).
    ok, err = backend.push_force_with_lease()
    if not ok:
        print(f"error: push failed: {err}", file=sys.stderr)
        return False

    return True


# ===========================================================================
# CLI
# ===========================================================================


def main(argv: list[str] | None = None) -> int:
    # Load GITHUB_TOKEN (and anything else) from ~/.env before we do
    # anything that might push.
    _load_env_file()

    parser = argparse.ArgumentParser(
        description="Squash the last N commits into one and force-push.",
    )
    parser.add_argument(
        "count",
        nargs="?",
        type=int,
        default=3,
        help="Number of commits to squash (default: 3).",
    )
    parser.add_argument(
        "-b",
        "--backend",
        default="subprocess",
        choices=[
            "subprocess",
            "pygithub",
            "gitpython",
            "libgit2",
            "dulwich",
            "dulwitch",
            "typer",
        ],
        help="Git backend (default: subprocess).",
    )
    args = parser.parse_args(argv)

    backend = build_backend(args.backend)
    ok = squash_commits(backend, args.count)

    if ok:
        print("pushed, done.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
