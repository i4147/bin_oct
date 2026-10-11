#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to recreate a Python script that fetches and displays a GitHub user's repositories, with the details needed to match its behavior.

Create a single-file Python 3 command-line script with a Termux-compatible shebang line (`#!/data/data/com.termux/files/usr/bin/env python`) and `from __future__ import annotations` at the top.

**Purpose:** The script retrieves the public repositories of a given GitHub user via the GitHub REST API, using the PyGithub library, and reports the results to the terminal. It should work with or without an authentication token.

**Dependencies:**
- `python-dotenv` (load environment variables from a `.env` file)
- `PyGithub` (the `github` package, providing `Auth`, `Github`, and `GithubException`)
- Standard library only otherwise: `json`, `sys`, `threading`, `time`, `os.getenv`, `pathlib.Path`

**Configuration:**
- Call `load_dotenv()` at startup so a `.env` file can supply a GitHub token (e.g., `GITHUB_TOKEN`) read via `getenv`.
- The token is optional. If present, authenticate with `Auth.Token(token)`; otherwise create an anonymous client.
- Use a configurable request timeout (default 60 seconds) passed to the Github client.

**Functions to implement:**

1. `countdown(timeout: int) -> None`
   - Runs as a daemon thread while the API request is in progress.
   - Prints `Timeout in N seconds... ` on a single line, overwriting with a carriage return (`\\r`), decrementing once per second from `timeout` down to 1.
   - After finishing, clears the line by writing 30 spaces followed by a carriage return, then flushes stdout.

2. `get_repos(username: str, token: str | None = None, timeout: int = 60) -> list`
   - Starts the `countdown` daemon thread with the timeout.
   - Creates the Github client (token-authenticated when a token is given, anonymous otherwise), both with the timeout.
   - Fetches the user with `get_user(username)` and returns `list(user.get_repos())`.
   - If the list is empty, prints `No public repositories found for user '<username>'.` (preceded by a newline) and returns an empty list.
   - Error handling for `GithubException` based on `e.status`:
     - 404: print `Error: User '<username>' not found.`
     - 401: print `Error: Invalid or expired token. Check your .env file.`
     - 403: if `"rate limit"` appears in the lowercased exception string, report a rate-limit message (advising the user to wait or add a token); otherwise report a generic access-forbidden message.
     - Other statuses: print a generic API error including the status and message.
   - Each error message is preceded by a newline and each handled path should return an empty list (or otherwise signal failure) so the caller can continue cleanly.
   - Handle other unexpected exceptions (e.g., network errors or timeouts) with a generic error message, returning an empty list.

**Main entry point (`if __name__ == "__main__":`):**
- Read the username from command-line arguments (`sys.argv`). If missing, print a usage message and exit with a non-zero status.
- Read the token from the environment via `getenv`, after `load_dotenv()`.
- Call `get_repos` and, when repositories are returned, output them. Each repository should be displayed with its name, description (or a placeholder if none), primary language, star count, fork status, and URL; the output may optionally be emitted as JSON (using `json.dumps` with indentation and `ensure_ascii=False`) when a flag is provided.
- Handle a keyboard interrupt (`Ctrl+C`) gracefully with a short message and a non-zero exit code.
- Exit with a non-zero status on failure and zero on success.

**Edge cases and behavior notes:**
- Usernames that do not exist, invalid tokens, rate-limit exhaustion, and network timeouts must each produce a clear message rather than a traceback.
- Users with zero public repositories must be reported without crashing.
- The countdown line must not corrupt normal output; always clear it before printing results or errors.
- Keep the script free of hardcoded credentials.
- Use type hints throughout, consistent with the `from __future__ import annotations` header.

**Usage:** Run as `python <script>.py <github_username>`, with optional `GITHUB_TOKEN` set in a `.env` file in the working directory.
---"""

from __future__ import annotations

import json
import sys
import threading
import time
from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from github import Auth, Github, GithubException


def countdown(timeout: int) -> None:
    for remaining in range(timeout, 0, -1):
        sys.stdout.write(f"\rTimeout in {remaining:2d} seconds... ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 30 + "\r")
    sys.stdout.flush()


def get_repos(username: str, token: str | None = None, timeout: int = 60) -> list:
    countdown_thread = threading.Thread(target=countdown, args=(timeout,), daemon=True)
    countdown_thread.start()
    try:
        if token:
            auth = Auth.Token(token)
            g = Github(auth=auth, timeout=timeout)
        else:
            g = Github(timeout=timeout)
        user = g.get_user(username)
        repos = list(user.get_repos())
        if not repos:
            print(f"\nNo public repositories found for user '{username}'.")
            return []
        return repos
    except GithubException as e:
        if e.status == 404:
            print(f"\nError: User '{username}' not found.")
        elif e.status == 401:
            print("\nError: Invalid or expired token. Check your .env file.")
        elif e.status == 403:
            if "rate limit" in str(e).lower():
                print("\nError: API rate limit exceeded. Use a token for higher limits.")
            else:
                print(f"\nError: Access forbidden. {e.data.get('message', '')}")
        else:
            print(f"\nGitHub API Error: {e.status} - {e.data.get('message', 'Unknown error')}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: script.py <username>")
        sys.exit(1)
    env_path = Path("~/.env").expanduser()
    load_dotenv(env_path)
    token = getenv("GITHUB_TOKEN")
    username = sys.argv[1]
    if token:
        print("Using authenticated access (rate limit: 5000 requests/hour)")
    else:
        print("No token found in .env, using unauthenticated access (rate limit: 60 requests/hour)")
    repos = get_repos(username, token=token, timeout=60)
    repos.sort(key=lambda r: r.stargazers_count, reverse=True)
    print(f"\nRepositories of '{username}' (sorted by stars):")
    for repo in repos:
        stars = repo.stargazers_count
        language = repo.language or "N/A"
        description = repo.description or "No description"
        print(f"- {repo.name}")
        print(f"  ⭐ {stars} | 🔤 {language} | {description[:80]}")
    json_data = [
        {
            "name": repo.name,
            "stars": repo.stargazers_count,
            "language": repo.language or "N/A",
            "description": repo.description or "No description",
            "url": repo.html_url,
        }
        for repo in repos
    ]
    json_filename = f"{username}.json"
    with Path(json_filename).open("w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)
    print(f"\nData successfully saved to {json_filename}")


if __name__ == "__main__":
    raise SystemExit(main())
