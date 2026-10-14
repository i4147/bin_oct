#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that downloads a GitHub repository as a ZIP archive for a specified user, repository, and branch, and saves it locally. The tool should be run from the command line and accept the repository owner, repository name, and an optional branch name (defaulting to the main branch), along with an optional custom output filename. It should authenticate to the GitHub API using a personal access token read from environment variables, which may also be loaded from a dotenv file in the user's home directory if present. If the token is missing, the script should stop with a clear error message and not attempt any network requests.
The script should connect to the specified repository, retrieve the repository archive for the requested branch, and report progress to the user as it runs, including the repository being accessed, the branch being fetched, and the approximate download size in megabytes. It should write the archive to disk under a sensible default filename derived from the repository and branch, or the user-provided name if given, and confirm the final saved location and file size on completion.
Error handling should be robust: if the repository or branch does not exist, if access is denied, or if any other GitHub API error occurs, the script should report a concise, user-friendly message rather than crashing with a raw traceback, and exit with a non-zero status code. Logging and console output should be clear and use simple status indicators, and the script should be structured as a reusable command-line utility with a main entry point.
---"""

from __future__ import annotations
import argparse
import logging
import os
from pathlib import Path
import sys
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
