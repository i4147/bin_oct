#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python CLI script that downloads a GitHub repository as a zip archive using the PyGithub library, authenticating via a GITHUB_TOKEN environment variable (optionally loaded from a .env file in the user's home directory).
It should accept the target username, repository name, branch (default "main"), and optional output filename as arguments, then connect to the repo, fetch the zipball for the specified branch, save it to disk, and print progress messages including download size in MB and the final saved file path.
The script must handle missing token and GitHub API errors gracefully by logging clear error messages and returning None instead of crashing, and should use argparse for command-line argument parsing and logging/print statements for user feedback with emoji indicators for success and failure states."""

from __future__ import annotations
import argparse
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from github import Github, GithubException

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
env_path = Path.home() / ".env"
if env_path.exists():
    load_dotenv(env_path)


def download_repo_zip(username: str, repo: str, branch: str = "main", output_name: str | None = None) -> Path | None:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("❌ Error: GITHUB_TOKEN environment variable not set.")
        return None
    g = Github(token)
    try:
        repo_full_name = f"{username}/{repo}"
        print(f"Connecting to repository: {repo_full_name}...")
        repo_obj = g.get_repo(repo_full_name)
        print(f"Fetching zipball for branch: {branch}...")
        zip_data = repo_obj.get_zipball(branch)
        size_mb = len(zip_data) / (1024 * 1024)
        print(f"📦 Download size: {size_mb:.2f} MB ({len(zip_data):,} bytes)")
        if output_name is None:
            output_name = f"{repo}-{branch}.zip"
        out_path = Path(output_name)
        out_path.write_bytes(zip_data)
        print(f"✅ Successfully downloaded: {out_path.absolute()}")
        return out_path
    except GithubException as e:
        logger.error(f"❌ GitHub Error: {e.data.get('message', str(e))}")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a GitHub repository as ZIP archive")
    parser.add_argument("repo", help='Repository in format "username/repo"')
    parser.add_argument("--branch", "-b", default="main", help="Branch name (default: main)")
    parser.add_argument("--output", "-o", help="Output filename")
    args = parser.parse_args()
    if "/" not in args.repo:
        logger.error("❌ Error: Repository must be in format 'username/repo'")
        sys.exit(1)
    username, repo = args.repo.split("/", 1)
    result = download_repo_zip(username, repo, args.branch, args.output)
    if not result:
        sys.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
