#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python 3.12 script (intended to run under Termux on Android, using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that automates pushing the current Git repository to GitHub while transparently injecting a GitHub personal access token for authentication.

The script's main purpose and behavior:

- Use `loguru` for logging, configured to remove the default handler and add a colorized stderr handler at INFO level.
- Define a `GitBackend` class that:
  - On initialization, sets `repo_path` to the current working directory (`Path.cwd()`).
  - Loads a GitHub token from a `~/.env` file by reading it, scanning lines for one starting with `GITHUB_TOKEN=`, and extracting the value (stripping whitespace and surrounding single/double quotes).
  - If `~/.env` does not exist, logs a warning and returns `None`.
  - If reading the file fails, logs an error with the exception and returns `None`.
  - If no valid token is found/loaded, logs an error (`GITHUB_TOKEN not found in ~/.env`) and exits the program immediately via `sys.exit(1)`.
  - Provides a `run` method that executes an arbitrary shell command (given as a list of arguments) using `subprocess.run`, capturing stdout/stderr as text. It copies the current environment variables, injects/overrides `GITHUB_TOKEN` with the loaded token, and runs the command with that environment. Before running, it logs the command being executed at DEBUG level. If `check=True` (the default) and the command returns a non-zero exit code, it logs an error including the command's stderr output.

Notable implementation details to preserve:
- Uses `from __future__ import annotations`, and imports `os`, `re`, `subprocess as sp`, `sys`, `pathlib.Path`, `typing.Optional`, and `loguru.logger`.
- Type hints are used throughout (e.g., `Optional[str]`, `list`, `sp.CompletedProcess`).
- The token file path is resolved via `Path.home() / ".env"`.
- The command list passed to `run` is joined with spaces for logging purposes.
- Designed to be extended further (e.g., for actual git push/remote operations) but the core responsibility shown is secure token loading from a local dotfile and safely wrapping subprocess calls with the token injected into the environment rather than hardcoded or passed as a CLI argument (to avoid leaking it in process listings or shell history).
- Error handling should be defensive: missing file, read errors, and missing token value should all be handled gracefully with appropriate log levels (warning for missing file, error for read failure or missing token), and a hard exit only occurs when no token could ultimately be loaded.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/KdPMoGXYBWNBrmyzEdCMfZ"""

from __future__ import annotations
import os
import re
import subprocess as sp
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", colorize=True)


class GitBackend:
    def __init__(self):
        self.repo_path = Path.cwd()
        self.github_token = self._load_github_token()
        if not self.github_token:
            logger.error("GITHUB_TOKEN not found in ~/.env")
            sys.exit(1)

    def _load_github_token(self) -> Optional[str]:
        env_file = Path.home() / ".env"
        if not env_file.exists():
            logger.warning(f"~/.env not found at {env_file}")
            return None
        try:
            content = env_file.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip("'\"")
                    if token:
                        logger.debug("Loaded GITHUB_TOKEN from ~/.env")
                        return token
        except Exception as e:
            logger.error(f"Failed to read ~/.env: {e}")
        return None

    def run(self, cmd: list, check: bool = True) -> sp.CompletedProcess:
        logger.debug(f"Running: {' '.join(cmd)}")
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = self.github_token
        result = sp.run(cmd, capture_output=True, text=True, env=env)
        if check and result.returncode != 0:
            logger.error(f"Command failed: {result.stderr}")
            sys.exit(1)
        return result

    def is_git_repo(self) -> bool:
        result = self.run(["git", "rev-parse", "--git-dir"], check=False)
        return result.returncode == 0

    def get_repo_name(self) -> str:
        return self.repo_path.name

    def init_repo(self):
        logger.info("Initializing git repository...")
        self.run(["git", "init"])

    def copy_gitignore(self):
        home_gitignore = Path.home() / ".gitignore"
        local_gitignore = self.repo_path / ".gitignore"
        if local_gitignore.exists():
            logger.debug(".gitignore already exists locally")
            return
        if home_gitignore.exists():
            logger.info(f"Copying .gitignore from {home_gitignore}")
            try:
                local_gitignore.write_text(home_gitignore.read_text())
            except Exception as e:
                logger.warning(f"Failed to copy .gitignore: {e}")
        else:
            logger.warning(f".gitignore not found at {home_gitignore}")

    def handle_submodules(self):
        gitmodules = self.repo_path / ".gitmodules"
        if not gitmodules.exists():
            logger.debug("No .gitmodules found")
            return
        logger.info("Found .gitmodules. Initializing submodules...")
        self.run(["git", "submodule", "init"])
        logger.info("Updating submodules recursively...")
        self.run(["git", "submodule", "update", "--init", "--recursive"])

    def get_remote_url(self) -> Optional[str]:
        result = self.run(["git", "remote", "get-url", "origin"], check=False)
        return result.stdout.strip() if result.returncode == 0 else None

    def get_remote_owner(self, url: str) -> Optional[str]:
        match = re.search(r"(?:github\.com[:/]|@github\.com:)([^/]+)", url)
        return match.group(1) if match else None

    def get_current_user(self) -> Optional[str]:
        result = self.run(["gh", "auth", "status", "-t"], check=False)
        if result.returncode == 0:
            match = re.search(r"as\s+(\S+)", result.stdout)
            return match.group(1) if match else None
        return None

    def remove_remote(self):
        logger.info("Removing origin remote...")
        self.run(["git", "remote", "remove", "origin"], check=False)

    def add_remote(self, url: str):
        logger.info(f"Adding remote: {url}")
        self.run(["git", "remote", "add", "origin", url])

    def create_github_repo(self, repo_name: str) -> str:
        logger.info(f"Creating GitHub repository '{repo_name}' on your account...")
        self.run(["gh", "repo", "create", repo_name, "--public", "--source=."])
        result = self.run(["gh", "repo", "view", "--json", "url", "-q", ".url"], check=False)
        if result.returncode == 0:
            url = result.stdout.strip()
            logger.info(f"Created repo: {url}")
            return url
        current_user = self.get_current_user()
        if current_user:
            url = f"git@github.com:{current_user}/{repo_name}.git"
            logger.info(f"Inferred repo URL: {url}")
            return url
        msg = "Failed to create GitHub repo or fetch URL"
        raise RuntimeError(msg)

    def add_all_files(self):
        logger.info("Staging all files...")
        self.run(["git", "add", "-A"])

    def has_changes(self) -> bool:
        result = self.run(["git", "status", "--porcelain"], check=False)
        return bool(result.stdout.strip())

    def commit(self, message: str):
        logger.info(f"Committing: {message}")
        self.run(["git", "commit", "-m", message])

    def get_current_branch(self) -> str:
        result = self.run(["git", "branch", "--show-current"], check=False)
        return result.stdout.strip() if result.returncode == 0 else "main"

    def push_upstream(self, branch: str) -> tuple[bool, Optional[str]]:
        logger.info(f"Pushing '{branch}' to origin...")
        result = self.run(["git", "push", "--set-upstream", "origin", branch], check=False)
        success = result.returncode == 0
        error = result.stderr if result.returncode != 0 else None
        return (success, error)

    def pull_rebase(self, branch: str):
        logger.info(f"Pulling '{branch}' with rebase...")
        self.run(["git", "pull", "origin", branch, "--rebase"])


class GitWorkflow:
    def __init__(self, backend: GitBackend):
        self.backend = backend

    def handle_remote_and_auth(self):
        current_url = self.backend.get_remote_url()
        current_user = self.backend.get_current_user()
        if not current_user:
            logger.error("Failed to authenticate with GitHub (gh auth)")
            sys.exit(1)
        logger.info(f"Authenticated as: {current_user}")
        if not current_url:
            logger.info("No remote configured. Will create new repo.")
            return False
        remote_owner = self.backend.get_remote_owner(current_url)
        logger.info(f"Current remote owner: {remote_owner}")
        if remote_owner and remote_owner != current_user:
            logger.warning(f"Remote configured for '{remote_owner}', but authenticated as '{current_user}'")
            self.backend.remove_remote()
            return False
        logger.info("Remote matches current user. Proceeding normally.")
        return True

    def execute(self):
        repo_name = self.backend.get_repo_name()
        logger.info(f"Repository: {repo_name}")
        if not self.backend.is_git_repo():
            self.backend.init_repo()
        else:
            logger.info("Git repository already initialized.")
        self.backend.copy_gitignore()
        self.backend.handle_submodules()
        keep_remote = self.handle_remote_and_auth()
        if not keep_remote:
            new_url = self.backend.create_github_repo(repo_name)
            self.backend.add_remote(new_url)
        self.backend.add_all_files()
        if self.backend.has_changes():
            self.backend.commit("initial: synced to new repo")
        else:
            logger.info("No changes to commit.")
        branch = self.backend.get_current_branch()
        success, error = self.backend.push_upstream(branch)
        if not success:
            logger.error(f"Push failed: {error}")
            if self._is_transient_error(error):
                logger.warning("Transient error detected. Retrying...")
                success, error = self.backend.push_upstream(branch)
            if not success:
                logger.error("Push failed after retry. Manual intervention needed.")
                sys.exit(1)
        logger.info(f"✅ Success! Pushed '{repo_name}' to GitHub")
        logger.info(f"   View at: https://github.com/{self.backend.get_current_user()}/{repo_name}")

    @staticmethod
    def _is_transient_error(error: Optional[str]) -> bool:
        if not error:
            return False
        transient_patterns = [
            "RPC failed",
            "curl",
            "HTTP2 framing",
            "send-pack",
            "disconnect",
            "hung up",
            "Connection reset",
            "Connection refused",
            "timeout",
            "temporarily unavailable",
        ]
        error_lower = error.lower()
        return any(pattern.lower() in error_lower for pattern in transient_patterns)


def main():
    try:
        backend = GitBackend()
        workflow = GitWorkflow(backend)
        workflow.execute()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
