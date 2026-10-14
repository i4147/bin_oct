#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that looks up the size of a GitHub repository and prints it in a human-readable form. The tool should accept either a full GitHub repository URL (for example, a link in the form https://github.com/owner/repo) or a short "owner/repo" identifier from the command line or standard input. It should validate the input format and print a clear message if the input is malformed. It should then query GitHub's public repository metadata to retrieve the reported size, which is provided in kilobytes, convert it to megabytes, and display the repository's owner and name alongside the size rounded to two decimal places. If the repository does not exist, the tool should report that clearly rather than crashing. For other network or API errors, such as connectivity problems, rate limiting, or unexpected server responses, it should fail gracefully with a concise, user-friendly error message. The script should be self-contained, runnable as a standalone command-line program, and written with clear, readable output suitable for both interactive use and scripting.
---"""

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
