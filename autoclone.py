#!/data/data/com.termux/files/usr/bin/env python
"""You are writing a self-contained prompt for an AI coding agent. Reproduce the following Python script from scratch, without access to its source. Describe it precisely enough that the agent can rebuild it.

Write a Python 3 script intended for the Termux environment on Android (shebang pointing to the Termux Python interpreter under /data/data/com.termux/files/usr/bin/). Use `from __future__ import annotations` at the top.

**Purpose:** The script inspects GitHub repositories and manages a local cache of their sizes. It fetches repository size information via the GitHub REST API and stores results in a JSON cache file so repeated runs avoid redundant API calls.

**Dependencies:** `requests` for HTTP calls and `python-dotenv` (`dotenv.load_dotenv`) for environment loading. Standard library modules: `os`, `subprocess`, `sys`, `datetime` (datetime and timedelta), `pathlib.Path`. Note that `json` is used in the cache loader but must be imported; the agent must ensure `import json` is present.

**Startup behavior:**
- Look for a `.env` file at the user's home directory (`~/.env`). If it exists, load it with `load_dotenv` and print a success message including the path, prefixed with a checkmark emoji. If not, print a warning (warning emoji) stating that the file was not found and system environment variables will be used.

**Constants:**
- `SIZE_CACHE_FILE` = `"repo_sizes.json"` (relative path in the current working directory).
- `CACHE_EXPIRY_DAYS` = `7`.

**Functions to implement:**

1. `get_github_token()`: Read the `GITHUB_TOKEN` environment variable. If present, print a success message and return it. Otherwise print a warning that no token was found, plus an indented note that unauthenticated requests are limited to 60 per hour, and return `None`.

2. `load_size_cache()`: If the cache file exists, open and parse it as JSON. Read the `_cache_date` key (ISO 8601 string, default `"2000-01-01"` if missing) using `datetime.fromisoformat`. If the cache is younger than `CACHE_EXPIRY_DAYS`, print how many repo entries were loaded (total keys minus the metadata key) and return the data dict. If expired, print a message that the cache is older than the expiry period and is being refreshed. Wrap parsing in error handling so malformed or unreadable files do not crash the script (the remaining behavior, including the fallthrough return of an empty or None value when the cache is invalid or missing, should return no cached data so the caller fetches fresh data).

**Notable behavior and conventions:**
- All user-facing output uses print statements with emoji status prefixes (✅, ⚠️, 📂, ⏰). Preserve this style.
- The cache stores a `_cache_date` metadata field alongside repo entries; entry count excludes this field.
- The script imports `subprocess` and `sys`, suggesting it may invoke external commands or exit with status codes; include these imports and use `sys.exit` for fatal errors where appropriate.
- Handle missing files, invalid JSON, invalid date strings, and network failures gracefully with clear printed messages.
- Include a `if __name__ == "__main__":` guard that runs the main workflow: load environment, obtain the token, load or refresh the cache, fetch repository sizes via the GitHub API with the token as a Bearer authorization header when available, update and save the cache with a fresh `_cache_date` timestamp, and print a summary.

**Output expectations:** A single runnable script with clear function separation, docstrings or brief comments, consistent emoji-prefixed console messages, and robust error handling for network, file, and parsing failures.
---"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

env_path = Path.home() / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print("⚠️  ~/.env not found, using system environment variables")
SIZE_CACHE_FILE = "repo_sizes.json"
CACHE_EXPIRY_DAYS = 7


def get_github_token():
    token = os.getenv("GITHUB_TOKEN")
    if token:
        print("✅ GitHub token found")
        return token
    else:
        print("⚠️  No GITHUB_TOKEN found in environment")
        print("   (Using unauthenticated requests - rate limit: 60/hr)")
        return None


def load_size_cache():
    cache_file = Path(SIZE_CACHE_FILE)
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)
                cache_date = datetime.fromisoformat(cache_data.get("_cache_date", "2000-01-01"))
                if datetime.now() - cache_date < timedelta(days=CACHE_EXPIRY_DAYS):
                    print(f"📂 Loaded cache from {SIZE_CACHE_FILE} ({len(cache_data) - 1} repos)")
                    return cache_data
                else:
                    print(f"⏰ Cache expired (older than {CACHE_EXPIRY_DAYS} days), refreshing...")
                    return {}
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"⚠️  Error reading cache file: {e}")
            return {}
    return {}


def save_size_cache(cache_data):
    cache_data["_cache_date"] = datetime.now().isoformat()
    cache_data["_cache_version"] = "1.0"
    try:
        with open(SIZE_CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=2)
        print(f"💾 Saved {len(cache_data) - 1} repository sizes to {SIZE_CACHE_FILE}")
    except Exception as e:
        print(f"⚠️  Error saving cache: {e}")


def get_repo_size(repo, token=None, cache_data=None):
    if cache_data and repo in cache_data:
        cached_size = cache_data[repo].get("size_mb")
        cached_date = cache_data[repo].get("fetched_at", "")
        if cached_size is not None:
            print(f"  📦 Using cached size: {cached_size:.2f} MB (fetched: {cached_date})")
            return cached_size
    api_url = f"https://api.github.com/repos/{repo}"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            size_kb = data.get("size", 0)
            size_mb = size_kb / 1024
            if cache_data is not None:
                cache_data[repo] = {
                    "size_mb": size_mb,
                    "size_kb": size_kb,
                    "fetched_at": datetime.now().isoformat(),
                    "repo_name": repo,
                    "full_name": data.get("full_name", repo),
                    "description": data.get("description", ""),
                    "private": data.get("private", False),
                }
            return size_mb
        elif response.status_code == 403 and "rate limit" in response.text.lower():
            print("  ⚠️  Rate limit exceeded! Please check your GITHUB_TOKEN")
            return None
        else:
            print(f"  ⚠️  Error fetching {repo}: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Error fetching {repo}: {e}")
        return None


def clone_repo(repo):
    clone_url = f"https://github.com/{repo}.git"
    repo_name = repo.split("/")[-1]
    if os.path.exists(repo_name):
        print(f"  ⏭️  {repo_name} already exists, skipping...")
        return True
    try:
        print(f"  🔄 Cloning {repo}...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", clone_url],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print(f"  ✅ Successfully cloned {repo_name}")
            return True
        else:
            print(f"  ❌ Failed to clone {repo}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout cloning {repo}")
        return False
    except Exception as e:
        print(f"  ❌ Error cloning {repo}: {e}")
        return False


def display_cached_stats(cache_data):
    if not cache_data or len(cache_data) <= 1:
        return
    repos = {k: v for k, v in cache_data.items() if k not in ["_cache_date", "_cache_version"]}
    if not repos:
        return
    sizes = [v["size_mb"] for v in repos.values() if "size_mb" in v]
    total_size = sum(sizes)
    avg_size = total_size / len(sizes) if sizes else 0
    largest = max(sizes) if sizes else 0
    smallest = min(sizes) if sizes else 0
    print("\n📊 Cache Statistics:")
    print(f"  📦 Total repos in cache: {len(repos)}")
    print(f"  📊 Total size: {total_size:.2f} MB")
    print(f"  📊 Average size: {avg_size:.2f} MB")
    print(f"  📈 Largest: {largest:.2f} MB")
    print(f"  📉 Smallest: {smallest:.2f} MB")
    print(f"  📅 Cached on: {cache_data.get('_cache_date', 'Unknown')}")


def main():
    fn = sys.argv[1]
    repos_file = Path(fn)
    if not repos_file.exists():
        print("❌ repos.txt not found in current directory")
        sys.exit(1)
    token = get_github_token()
    cache_data = load_size_cache()
    with open(repos_file) as f:
        repos = [line.strip() for line in f if line.strip()]
    if not repos:
        print("❌ No repositories found in repos.txt")
        sys.exit(1)
    print(f"\n📚 Found {len(repos)} repositories")
    print("🔍 Checking and cloning in one pass...")
    print("-" * 40)
    size_limit_mb = 5
    cloned_count = 0
    skipped_count = 0
    failed_count = 0
    total_size = 0
    no_size_count = 0
    for idx, repo in enumerate(repos, 1):
        repo_lower = repo.lower()
        if "django" in repo_lower or "flask" in repo_lower:
            skipped_count += 1
            continue
        if "torch" in repo_lower or "tensor" in repo_lower:
            skipped_count += 1
            continue
        if "llm" in repo_lower or "mcp" in repo_lower:
            skipped_count += 1
            continue
        print(f"\n[{idx}/{len(repos)}] 📦 Processing {repo}")
        print("-" * 40)
        size_mb = get_repo_size(repo, token, cache_data)
        if size_mb is None:
            no_size_count += 1
            continue
        print(f"  📊 {size_mb:.2f} MB")
        if size_mb > size_limit_mb:
            skipped_count += 1
            continue
        print(f"  ✅ Within limit ({size_limit_mb} MB)")
        total_size += size_mb
        if clone_repo(repo):
            cloned_count += 1
        else:
            failed_count += 1
    if cache_data:
        save_size_cache(cache_data)
        display_cached_stats(cache_data)
    print("\n" + "=" * 40)
    print("📊 FINAL SUMMARY")
    print("-" * 40)
    print(f"✅ Successfully cloned: {cloned_count}")
    print(f"❌ Failed to clone: {failed_count}")
    print(f"⏭️  Skipped (too large): {skipped_count}")
    print(f"⚠️  Skipped (no size info): {no_size_count}")
    print(f"📊 Total size of cloned repos: {total_size:.2f} MB")
    print(f"📚 Total repos processed: {len(repos)}")
    if token:
        print("\n💡 Using authenticated requests (rate limit: 5000/hr)")
    else:
        print("\n💡 Using unauthenticated requests (rate limit: 60/hr)")
        print("   Consider adding GITHUB_TOKEN to ~/.env for higher limits")
    print(f"\n💾 Repository size data saved to: {SIZE_CACHE_FILE}")


if __name__ == "__main__":
    raise SystemExit(main())
