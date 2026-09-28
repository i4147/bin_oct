#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that fetches a GitHub user's public repositories using the GitHub REST API and writes a formatted summary to a text file.
It should take a username and an output file path as inputs, calling the GitHub API endpoint for that user's repos, and for each repository record its name, description, URL, star count, fork count, and primary language.
The script must handle cases where no repositories are found, and gracefully catch and report network request errors and JSON parsing errors, printing a success message with the repository count once the file is written."""

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
