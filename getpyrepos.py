#!/data/data/com.termux/files/usr/bin/env python
"""The Python code you pasted is cut off partway through the `get_user_repos` function's exception handling (it ends at `requests.exceptions.RequestExcepti`), so I can only describe the part that's visible. Here is the prompt, based on that visible portion:

Write a self-contained Python 3 script, intended to run under Termux on Android (use a `#!/data/data/com.termux/files/usr/bin/env python` shebang), that fetches the public GitHub repositories of a given user and keeps only those whose primary language is Python.

Requirements:

- Begin the file with the Termux-specific shebang line and `from __future__ import annotations` so type hints like `list[dict]` work on older Python versions.
- Import only the standard library modules `json`, `sys`, and `datetime` (including `datetime` and `timedelta`), plus the third-party `requests` package.
- Implement a function `get_user_repos(username: str) -> list[dict]` that pages through the GitHub REST API endpoint `https://api.github.com/users/{username}/repos` using `requests.get` with query parameters `page` (starting at 1), `per_page` set to 100, and `sort` set to `updated`.
- For each page, call `raise_for_status()` on the response and parse the JSON body. Stop paginating when a page returns an empty list, or when a page contains fewer than 100 items.
- For each repository on a page, include it in the results only if its `language` field equals `"Python"`. For each included repository, build a dictionary with these keys and values taken from the API response: `name`, `full_name`, `description` (defaulting to an empty string when missing), `url` (from `html_url`), `stars` (from `stargazers_count`), `forks` (from `forks_count`), `language`, `created_at`, `updated_at`, and `private`.
- Wrap the request and parsing logic in a `try` block that catches `requests.exceptions.RequestException` (and any other requests-related errors as appropriate), reporting the failure rather than crashing silently. The exact handling of the error branch should be completed by the agent in a sensible way: print a clear error message to stderr, and return whatever repositories were collected or exit with a non-zero status.
- Read the target username from the command line arguments via `sys.argv`, and print a usage message and exit with a non-zero status if it is missing.
- Output the collected repositories as pretty-printed JSON to standard output using `json.dumps`, with non-ASCII characters preserved.
- Optionally use `datetime` and `timedelta` to format or filter timestamps if helpful, but the core behavior is listing Python repositories.
- Handle edge cases: users with no repositories, users with no Python repositories (output an empty JSON list), repositories with a null description, and private repositories appearing in the response.
- Add concise comments and docstrings consistent with a small utility script, and keep the code idiomatic and readable.
- Make the script executable as a standalone command with `python script.py <username>`, and include a `main` guard so it can also be imported without side effects.
---"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta

import requests


def get_user_repos(username: str) -> list[dict]:
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos"
        params = {"page": page, "per_page": 100, "sort": "updated"}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            page_repos = response.json()
            if not page_repos:
                break
            for repo in page_repos:
                if repo.get("language") == "Python":
                    repos.append({
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description", ""),
                        "url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "language": repo["language"],
                        "created_at": repo["created_at"],
                        "updated_at": repo["updated_at"],
                        "private": repo["private"],
                    })
            if len(page_repos) < 100:
                break
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repos for {username}: {e}", file=sys.stderr)
            break
    return repos


def get_top_trending_users() -> list[dict]:
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = "https://api.github.com/search/users"
    params = {
        "q": f"language:python created:>{week_ago}",
        "sort": "followers",
        "order": "desc",
        "per_page": 10,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        trending_users = []
        for user in data.get("items", []):
            user_url = user["url"]
            user_response = requests.get(user_url)
            user_response.raise_for_status()
            user_data = user_response.json()
            trending_users.append({
                "username": user_data["login"],
                "name": user_data.get("name", ""),
                "followers": user_data["followers"],
                "repos_url": user_data["repos_url"],
                "html_url": user_data["html_url"],
                "repositories": get_user_repos(user_data["login"]),
            })
        return trending_users
    except requests.exceptions.RequestException as e:
        print(f"Error fetching trending users: {e}", file=sys.stderr)
        return []


def save_to_json(data: any, filename: str = "github_repos.json") -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {filename}")


def main():
    if len(sys.argv) > 1:
        username = sys.argv[1]
        print(f"Fetching Python repositories for user: {username}")
        repos = get_user_repos(username)
        if repos:
            output = {
                "username": username,
                "total_python_repos": len(repos),
                "repositories": repos,
            }
            filename = f"{username}_python_repos.json"
            save_to_json(output, filename)
            print(f"Found {len(repos)} Python repositories")
        else:
            print(f"No Python repositories found for user {username}")
    else:
        print("No username provided. Fetching top trending GitHub users with Python repos...")
        trending_data = get_top_trending_users()
        if trending_data:
            output = {
                "timestamp": datetime.now().isoformat(),
                "trending_users": trending_data,
            }
            save_to_json(output, "trending_github_python_users.json")
            print(f"Found {len(trending_data)} trending users")
            for user in trending_data:
                print(f"\n👤 {user['username']} ({user['name']})")
                print(f"   Followers: {user['followers']}")
                print(f"   Python repos: {len(user['repositories'])}")
        else:
            print("No trending users found")


if __name__ == "__main__":
    raise SystemExit(main())
