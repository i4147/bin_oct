#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that accepts a single argument representing a GitHub repository, either in "user/repo" shorthand or as a full "https://github.com/user/repo" URL, parsing the URL with a regular expression when needed to extract the username and repository name.
The script should query the GitHub REST API for that repository's metadata, then compute and print the repository size in megabytes (converted from the "size" field returned in kilobytes) along with the repository identifier.
It must gracefully handle invalid input formats, a 404 not-found response, and general request exceptions by printing descriptive error messages, and it should validate that exactly one command-line argument is provided, printing usage instructions and exiting with status code 1 otherwise."""

from __future__ import annotations
import re
import sys
import requests


def get_repo_size(input_str: str) -> None:
    if input_str.startswith("https://github.com/"):
        match = re.search(r"github\.com/([^/]+)/([^/]+)", input_str)
        if not match:
            print("Invalid GitHub URL format.")
            return
        user, repo = match.groups()
    else:
        parts = input_str.split("/")
        if len(parts) != 2:
            print("Invalid format. Use 'user/repo' or full URL.")
            return
        user, repo = parts
    url = f"https://api.github.com/repos/{user}/{repo}"
    try:
        response = requests.get(url)
        if response.status_code == 404:
            print(f"Repository '{user}/{repo}' not found.")
            return
        response.raise_for_status()
        data = response.json()
        size_kb = data.get("size", 0)
        size_mb = size_kb / 1024
        print(f"Repository: {user}/{repo}")
        print(f"Size: {size_mb:.2f} MB")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get-repo-size <user/repo> or <https://github.com/user/repo>")
        sys.exit(1)
    get_repo_size(sys.argv[1])
