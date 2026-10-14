#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that queries the GitHub repository search service for the 50 most recently updated public repositories written in Python, then saves a plain-text report of those results to a local file and reports where the file was saved.
The script should:
- Load a GitHub access token from a configuration file located in the user's home directory, falling back to an environment variable if needed, and authenticate requests with it.
- Request the latest 50 Python repositories, sorted by most recent update time in descending order.
- Raise a clear error and stop if the remote service returns a failure response, rather than silently producing incomplete output.
- Write results to a text file named "ghpy.txt" in the current working directory. The file should begin with a title line, a separator line of equal signs, and a blank line. Each repository entry should include its full name, its web URL, its last-updated timestamp, and its star count, indented beneath the name and followed by a blank line for readability.
- Print a short confirmation message to the console indicating the output file location once writing is complete.
- Run its main logic only when executed directly as a program, not when imported as a module.
Keep the implementation simple, readable, and self-contained, with clear handling of missing credentials or network problems so the user understands what went wrong.
---"""

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
import requests


def search_python_repos():
    load_dotenv(Path.home() / ".env")
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "q": "language:Python",
        "sort": "updated",
        "order": "desc",
        "per_page": 50,
    }
    response = requests.get("https://api.github.com/search/repositories", headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    output = Path("ghpy.txt")
    with output.open("w") as f:
        f.write("50 most active py repos\n")
        f.write("=" * 40 + "\n\n")
        for repo in data["items"]:
            f.write(f"{repo['full_name']}\n")
            f.write(f"  URL: {repo['html_url']}\n")
            f.write(f"  Updated: {repo['updated_at']}\n")
            f.write(f"  Stars: {repo['stargazers_count']}\n\n")
    print(f"Results saved to {output}")


if __name__ == "__main__":
    search_python_repos()
