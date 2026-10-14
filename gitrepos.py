#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that fetches the public repositories of a given GitHub user and saves a human-readable summary of them to a text file.
The tool should accept a GitHub username and an optional output file path. It should query GitHub's public API for that user's repositories and handle the case where the user has no repositories by informing the user without creating an empty report. For each repository, the report should include the repository name, a description (with a fallback message when none is provided), its web URL, star count, fork count, and primallback when unspecified). The output should begin with a header identifying the username and a visual separator, followed by one clearly delineated entry per repository.
Handle network failures and error responses from the API gracefully, reporting a clear message to the user rather than crashing. When no output file is specified, the script should choose a sensible default filename derived from the username. Output text should be UTF-8 encoded so that non-ASCII repository descriptions are preserved. The script should be runnable from the command line, taking the username (and optionally the output path) as arguments, and should print a confirmation message with the location of the saved file upon success.
---"""

from __future__ import annotations
import json
from pathlib import Path
import requests


def get_github_repos(username: str, output_file=None) -> None:
    if output_file is None:
        url = f"https://api.github.com/users/{username}/repos"
    try:
        response = requests.get(url)
        response.raise_for_status()
        repos = response.json()
        if not repos:
            print(f"No repositories found for user: {username}")
            return
        with Path(output_file).open("w", encoding="utf-8") as f:
            f.write(f"GitHub repositories for user: {username}\n")
            f.write("=" * 40 + "\n\n")
            for repo in repos:
                name = repo["name"]
                description = repo["description"] or "No description"
                url = repo["html_url"]
                stars = repo["stargazers_count"]
                forks = repo["forks_count"]
                language = repo["language"] or "Not specified"
                f.write(f"Repository: {name}\n")
                f.write(f"Description: {description}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Stars: {stars} | Forks: {forks} | Language: {language}\n")
                f.write("-" * 40 + "\n")
        print(f"Successfully saved {len(repos)} repositories to {output_file}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    username = input("Enter GitHub username: ").strip()
    get_github_repos(username)
