#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that reports the size of a GitHub repository. It must run on Termux (Android) under a Termux-style Python shebang, and it uses only the standard library's regex, system-argument, and future-annotations features plus the third-party requests package.

Behavior and requirements:

1. Entry point: the script runs when executed directly. It expects exactly one command-line argument (besides the script name). If the argument count is not exactly two, print a usage message in the form "Usage: python get-repo-size <user/repo> or <https://github.com/user/repo>" and exit with status code 1.

2. Input parsing: the single argument is either a full GitHub URL beginning with "https://github.com/" or a shorthand "user/repo" string.
   - For a full URL, extract the owner and repository name with a regular expression matching the github.com domain followed by two path segments (owner and repo, each being non-slash characters). Extra path segments after the repo (such as /tree/main) should be ignored. If the regex does not match, print "Invalid GitHub URL format." and return without error.
   - For a shorthand, split on "/" and require exactly two parts. If the count is not two, print "Invalid format. Use 'user/repo' or full URL." and return. Do not otherwise validate characters.

3. API request: build the URL "https://api.github.com/repos/{user}/{repo}" and perform an HTTP GET with the requests library, with no custom headers, authentication token, or timeout.
   - If the response status is 404, print "Repository '{user}/{repo}' not found." and return.
   - Otherwise call raise_for_status so that other HTTP errors raise an exception.
   - Parse the response body as JSON and read the "size" field (defaulting to 0 if missing). GitHub reports this size in kilobytes.

4. Output: convert kilobytes to megabytes by dividing by 1024. Print two lines:
   - "Repository: {user}/{repo}"
   - "Size: {size_mb} MB" where size_mb is formatted with exactly two decimal places.

5. Error handling: wrap the network request and parsing in a try block catching the requests library's base RequestException. On such an error, print "Error fetching data: " followed by the exception message. Do not catch other exception types.

6. Style: use postponed evaluation of type annotations (from __future__ import annotations). The main function takes a string and returns nothing, with type hints. Use a Termux-specific shebang line pointing to the Termux Python interpreter path. Keep the whole program in a single file with no classes and no external configuration. Use only print for output, with no logging module.

7. Usage examples the script should support:
   - python get-repo-size psf/requests
   - python get-repo-size https://github.com/psf/requests

Deliver the script as one self-contained Python file implementing exactly this behavior.
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
