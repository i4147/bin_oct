#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that searches GitHub for Python repositories created within the last 10 days, sorted by star count in descending order, using the GitHub REST API.
It should load a GITHUB_TOKEN from a .env file in the user's home directory for authentication, fetch up to 50 results via requests, and raise an error if the token is missing.
The script should write each repository's full name and star count to a local file named "ghpy10.txt" and print a confirmation message showing how many repositories were saved.
"""

from __future__ import annotations
import os
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv


def search_github_repos() -> None:
    env_path = Path.home() / ".env"
    load_dotenv(env_path)
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        msg = f"GITHUB_TOKEN not found in {env_path}"
        raise ValueError(msg)
    date_10_days_ago = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    query = f"language:Python created:>{date_10_days_ago}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 50}
    response = requests.get("https://api.github.com/search/repositories", headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    output_file = Path("ghpy10.txt")
    with output_file.open("w") as f:
        for repo in data["items"]:
            f.write(f"{repo['full_name']} - {repo['stargazers_count']} stars\n")
    print(f"✓ Saved {len(data['items'])} repos to ghpy10.txt")


if __name__ == "__main__":
    search_github_repos()
