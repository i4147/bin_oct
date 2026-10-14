#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that searches GitHub for recently created Python repositories and saves a ranked list of them to a text file. The script should load a GitHub API access token from a environment configuration file located in the user's home directory, and fail with a clear error message if the token is missing. It should look for public repositories whose primary language is Python and that were created within the last 10 days, ordered by star count from highest to lowest, retrieving up to 50 results. Authenticate requests to the GitHub REST search API using the token, and handle HTTP errors so that failed requests are reported clearly rather than silently producing bad output. Write each matching repository's full name (owner and repository name) on its own line into an output file named "ghpy10.txt" in the current working directory, overwriting any previous contents. Keep the implementation simple and self-contained, and make sure the script runs as a standalone command-line program.
---"""

from __future__ import annotations
from datetime import datetime, timedelta
import os
from pathlib import Path
from dotenv import load_dotenv
import requests


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
