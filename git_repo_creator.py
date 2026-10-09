#!/data/data/com.termux/files/usr/bin/env python
""".dumps(payload).url, method=method, data=data)
    request.add_header("Authorization", f"token {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("User-Agent", "repo-init-script")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request) as response: = response.read()
            return response.status, json.loads(body) if body = exc.read()
        try:
            parsed = json.loads( if body else None
        except json.JSONDecodeError:
            parsed = body.decode(errors="replace")
        return exc.code, parsed

def create_github_repo(name: str, token: str, private: bool, description: str) -> Dict[str, Any]:
    status, body = api_request(
        "POST",
        "https://api.github.com/user/repos",
        token,
        {"name": name, "private": private, "description": description, "auto_init": False},
    )
    if status == 201:
        return body
    if status == 422 and isinstance(body, dict) and "already exists" in jsonower():
        print(f"Repo '{name}' already exists on GitHub, contin")
        status2, body2 = api_request("Ggithub.com/repos/{{owner}}/{name}", token)
        return body2 if status2 == 200 else {": name}
    print(f"G({status}): {body}",)
    sys.exittoken: str) -> str:body, dict):
        return
    print(f"Errorenticated user: {body}", file=sys.stderit(1)

def init_git_repo(project_dir: Path, remote_url: str, branch: str) -> None:
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        run(["git", "init"], cwd=project_dir, check=True)
    run(["git", "checkout", "-B", branch], cwd=project_dir, check=True)
    result = run(["git", "remote", "get-url", "origin"], cwd=project_dir)
    if result.returncode == 0:
        run(["git", "remote",", remote_url], cw=True)
    else:
        run(["git", "remote", "add", "origind=project_dir, check=True)

def ensure_gitignore(project_dir: Path) -> = project_dir / ". gitignore.exists():pycache__/
*.env
.DS_Store
.vscode/
\"\"\"
    gitignore.write_text(content)

def ensure_readme(project_dir: Path, name: str, description: str) -> None:
    readme = project_dir / "README.md"
    if readme.exists():
        return
    created = datetime.now().strftime("%Y-%m-%d")
    content = f\"\"\"# {name}

{description or "Project description."}

Created: {created}
\"\"\"
    readme.write_text(content)

def commit_and_push(project_dir: Path, branch: str) -> None:
    run(["git", "add", "-A"], cwd=project_dir, check=True)
    result = run(["git", "diff", "--cached", "--quiet"], cwd=project_dir)
    if result.returncode != 0:
        run(["git", "commit", "-m", "Initial commit"], cwd=project_dir, check=True)
    else:
        print("Nothing to commit, skipping commit step.")
    push_result = run(["git", "push", "-u", "origin", branch], cwd=project_dir, check=False, capture=False
        print("ning: git push failed. You may need to push manually.",)_g") is not None

def main() = argparse.ArgInitialize a local project and push it to a")
    parser.add_/repo name")
    parser", default="", help="Rep description")
    parser.add_argument("--private", action private repository")
    parser.add_argument("--branch", default="main", help="Default branch name")
    , help="Project.add_argument("--tokenitHub token/.env)")
    parser.add_argument("--env-file", default="~/.env", help="Path to .env file containing GITHUB_TOKEN")
    args = parser.parse_args()

    project_dir = Path(args.path).expanduser() if args.path else Path.cwd() / args.name
    project_dir.mkdir(parents=True, exist_ok=True)

    token = get_token(args)

    print(f"Creating GitHub repository '{args.name}'...")
    repo = create_github_repo(args, args.description)
    owner = repo.get("owner", { get_authenticated_usero.get("ssh_url") and False:
        pass

    print(f"Set at {project_dir}...itignore(project_dir)
    ensure_read.name, args.name False else args.descriptiono(project_dir, rem
    commit_and_push(project_dir, args.name False else args.branch) at:o.get("owhtml_url") or f'https://github.com/{__ == "__main__":
    main()

Write a_disable_html"

Write a prompt for an AI coding agent to generate a Python 3.12 command-line script (designed to run under Termux on Android, using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that automates creating a new GitHub repository and initializing/pushing a local project to it.

The script should use only standard library modules: `argparse`, `json`, `os`, `shutil`, `subprocess`, `sys`, `urllib.request`/`urllib.error`, `datetime`, `pathlib`, and `e the following requirements for implement:

**Pur: A CLI tool that, the GitHub REST API, sets up a local project if missing), initializes git, and commits and pushes the initial contentitHub.

**C `argparse`):
-ional,
- `--description` (default): repository description.
- `--private` (flag):branch` (default `" to createls back to `./<name> `--token` (default `None`): GitHub personal.env.
- `--env-file` (default `"~/.env"`): path to a `.env`-style file that may contain `GITHUB_TOKEN`.

**Token resolution logic**: Resolve the GitHub token in this priority order: `--token` argument, then `GITHUB_TO `GITHUB_Try parsed from the `.env` file (simple `KEY=VALUE strips surrounding quot token is found, print an error to stderr and exit with status API interaction**ic auth `urllib.request` (raries) that sends JSloads, sets `Authorization: token <TOKEN>`, ` a `User-Agent`or raw text) body, gracefully hand still parsing/ body.

**Repository creation**: Use the G (`POST / a repository disabled). If the repoHTTP 422 with an "already exists" styleead of failing. On any other API error, print the error and exit with a non-zero status.

**Authenticated user lookup**: Provide a helper that calls `GET /user` to retrieve the authenticated username, used as a fallback when determining the repo owner for constructing URLs, exiting with an error if this call fails.

**Local git setup**:
- Create the project directory (including parents) if it doesn't exist.
- Initialize a git repository if ` exist.
- Create/ified branch. or update the `origin` rem to the repo's HTTPS clone URL. `.gitignore` (S/
- Write a default `README.md` (with project name, description or a placeholder, and the comm only if there are sta that there's nothing to commit), then push to `origin` on the specified branch with upstream tracking set; if the push fails, print a warning to stderr instead of crashing.

**Utilities**: Include a small subprocess wrapper for running shell commands with consistent options (working directory, output capture, error checking), and a helper to check whether the `gh` CLI is available on the system (even if not strictly required by the main flow).

**Output/flow**: Print progress messages at each major step (creating repo, setting up local project, etc.) and a final confirmation message showing the repository's URL on GitHub. The script's `main()` function should orchestrate argument parsing, token resolution, repo creation, local setup, and commit/push in sequence, and run under the standard `if __name__ == "__main__":` guard.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/4ezbx9ZjMzYX9SHBpz4ceJ"""

from __future__ import annotations
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, Optional, Sequence
import urllib.error
import urllib.request


def run(
    cmd: Sequence[str], cwd: Optional[Path] = None, check: bool = False, capture: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(cmd), cwd=str(cwd) if cwd else None, check=check, text=True, capture_output=capture)


def load_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def get_token(args: argparse.Namespace) -> str:
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        env_path = Path(args.env_file).expanduser()
        token = load_env(env_path).get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not found in ~/.env", file=sys.stderr)
        sys.exit(1)
    return token


def api_request(method: str, url: str, token: str, payload: Optional[dict[str, Any]] = None) -> tuple[int, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, method=method, data=data)
    request.add_header("Authorization", f"token {token}")
    request.add_header("Accept", "application/vnd.github.v3+json")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"message": body}
        return exc.code, parsed


def create_repo_api(
    token: str, name: str, description: str, private: bool, auto_init: bool, api_url: str
) -> Optional[dict[str, Any]]:
    payload = {"name": name, "description": description, "private": private, "auto_init": auto_init}
    status, data = api_request("POST", api_url, token, payload)
    if status == 201:
        print("✅ Repository created successfully!")
        print(f"📁 Name:{data['name']}")
        print(f"🔗 URL:{data['html_url']}")
        print(f"📝 Clone URL:{data['clone_url']}")
        return data
    print(f"❌ Failed to create repository:{status}")
    print(f"Error:{data.get('message', 'Unknown error')}")
    return None


def git_repo_exists(cwd: Path) -> bool:
    return (cwd / ".git").exists()


def init_git(cwd: Path, git_user: Optional[str] = None, git_email: Optional[str] = None) -> None:
    if not git_repo_exists(cwd):
        print("Initializing git repository...")
        run(["git", "init"], cwd, check=True)
    else:
        print("Git repository already initialized.")
    if git_user:
        run(["git", "config", "user.name", git_user], cwd)
    if git_email:
        run(["git", "config", "user.email", git_email], cwd)


def stage_all(cwd: Path) -> None:
    print("Staging all changes...")
    run(["git", "add", "-A"], cwd, check=True)


def commit(cwd: Path, message: str) -> bool:
    status = run(["git", "status", "--porcelain"], cwd)
    if status.stdout.strip():
        print("Committing changes...")
        run(["git", "commit", "-m", message], cwd, check=True)
        return True
    print("No changes to commit.")
    return False


def rename_branch(cwd: Path, branch: str) -> None:
    current = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if current.returncode == 0 and current.stdout.strip() != branch:
        print(f"Renaming branch from '{current.stdout.strip()}' to '{branch}'...")
        run(["git", "branch", "-M", branch], cwd)


def add_or_set_remote(cwd: Path, url: str, remote: str) -> None:
    current = run(["git", "remote", "get-url", remote], cwd)
    if current.returncode == 0:
        existing = current.stdout.strip()
        if existing != url:
            print(f"Updating remote {remote} from {existing} to {url}")
            run(["git", "remote", "set-url", remote, url], cwd)
        else:
            print(f"Remote '{remote}' already configured correctly")
    else:
        print(f"Adding remote {remote}: {url}")
        run(["git", "remote", "add", remote, url], cwd, check=True)


def push(cwd: Path, remote: str, branch: str, pull_rebase: bool) -> None:
    print(f"Pushing branch '{branch}' to {remote}...")
    result = run(["git", "push", "-u", remote, branch], cwd)
    if result.returncode == 0:
        print("Successfully pushed.")
        return
    error = (result.stderr or "") + (result.stdout or "")
    if pull_rebase and (
        "non-fast-forward" in error or "fetch first" in error or "remote contains work" in error or "rejected" in error
    ):
        print("Remote has changes. Pulling with rebase...")
        run(["git", "pull", remote, branch, "--rebase"], cwd, check=True)
        run(["git", "push", "-u", remote, branch], cwd, check=True)
        print("Successfully pushed after rebase.")
        return
    print(error, file=sys.stderr)
    sys.exit(1)


def gh_available() -> bool:
    return shutil.which("gh") is not None


def gh_authenticated() -> bool:
    return run(["gh", "auth", "status"]).returncode == 0


def gh_repo_exists(username: Optional[str], name: str) -> bool:
    full = f"{username}/{name}" if username else name
    return run(["gh", "repo", "view", full]).returncode == 0


def gh_create_repo(name: str, source: Path, remote: str, public: bool, description: Optional[str]) -> None:
    cmd = ["gh", "repo", "create", name, "--source", str(source), "--remote", remote]
    cmd.append("--public" if public else "--private")
    if description:
        cmd.extend(["--description", description])
    print(f"Running:{' '.join(cmd)}")
    result = run(cmd)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)


def ensure_readme(cwd: Path, name: str) -> None:
    files = [path for path in cwd.iterdir() if path.name != ".git"]
    if not files:
        readme = cwd / "README.md"
        if not readme.exists():
            readme.write_text(f"# {name}\nRepository initialized on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            print("Created README.md")


def copy_gitignore(cwd: Path) -> None:
    global_gitignore = Path.home() / ".gitignore"
    local_gitignore = cwd / ".gitignore"
    if global_gitignore.exists() and not local_gitignore.exists():
        shutil.copy2(global_gitignore, local_gitignore)
        print(f"Copied {global_gitignore}->{local_gitignore}")
    elif local_gitignore.exists():
        print(".gitignore already exists in current directory.")
    else:
        print(f"No global .gitignore found at {global_gitignore}")


def add_bool_argument(parser: argparse.ArgumentParser, name: str, default: bool) -> None:
    dest = name.replace("-", "_")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(f"--{name}", dest=dest, action="store_true")
    group.add_argument(f"--no-{name}", dest=dest, action="store_false")
    parser.set_defaults(**{dest: default})


def cmd_api(args: argparse.Namespace) -> int:
    token = get_token(args)
    name = args.name or Path.cwd().name
    data = create_repo_api(token, name, args.description, args.private, args.auto_init, args.api_url)
    if not data:
        return 1
    if args.push:
        cwd = Path.cwd()
        init_git(cwd, args.git_user, args.git_email)
        stage_all(cwd)
        commit(cwd, args.commit_message)
        rename_branch(cwd, args.branch)
        url = data["clone_url"] if args.protocol == "https" else data["ssh_url"]
        add_or_set_remote(cwd, url, args.remote)
        push(cwd, args.remote, args.branch, args.pull_rebase)
        print(f"\n✨ Repository ready at:{data['html_url']}")
    return 0


def cmd_gh(args: argparse.Namespace) -> int:
    cwd = Path(args.source).expanduser().resolve()
    os.chdir(cwd)
    if not gh_available():
        print("Error: GitHub CLI (gh) is not installed.", file=sys.stderr)
        return 1
    if not gh_authenticated():
        print("Error: GitHub CLI is not authenticated. Run: gh auth login", file=sys.stderr)
        return 1
    repo_name = args.name or cwd.name
    if args.copy_global_gitignore:
        copy_gitignore(cwd)
    if not git_repo_exists(cwd):
        if args.init:
            init_git(cwd, args.git_user, args.git_email)
        else:
            print("Error: not a git repository and --no-init", file=sys.stderr)
            return 1
    else:
        if args.existing == "exit":
            return 0
        if args.existing == "ask":
            if sys.stdin.isatty():
                print(f"Git repository already exists in {cwd}")
                print("1. Merge changes")
                print("2. Create new repository")
                print("3. Exit")
                choice = input("Select option (1-3): ").strip()
                if choice == "3":
                    return 0
                if choice == "2":
                    new_name = input("Enter new repository name: ").strip()
                    if not new_name:
                        print("Error: Repository name cannot be empty.", file=sys.stderr)
                        return 1
                    repo_name = new_name
                    run(["git", "remote", "remove", args.remote], cwd)
        elif args.existing == "new":
            if args.name:
                repo_name = args.name
            else:
                new_name = input("Enter new repository name: ").strip()
                if not new_name:
                    print("Error: Repository name cannot be empty.", file=sys.stderr)
                    return 1
                repo_name = new_name
            run(["git", "remote", "remove", args.remote], cwd)
    if args.create_readme:
        ensure_readme(cwd, repo_name)
    if args.commit:
        stage_all(cwd)
        message = args.commit_message or datetime.now().strftime("Auto-commit:%Y-%m-%d:%H:%M:%S")
        commit(cwd, message)
    if args.rename_branch:
        rename_branch(cwd, args.branch)
    if args.push:
        if not gh_repo_exists(args.github_username, repo_name):
            gh_create_repo(repo_name, cwd, args.remote, not args.private, args.description)
        else:
            print(f"✓ Repository {repo_name} already exists on GitHub")
        if args.github_username:
            url = (
                f"git@github.com:{args.github_username}/{repo_name}.git"
                if args.protocol == "ssh"
                else f"https://github.com/{args.github_username}/{repo_name}.git"
            )
            add_or_set_remote(cwd, url, args.remote)
        push(cwd, args.remote, args.branch, args.pull_rebase)
        print(f"\n✅ Success! Repository '{repo_name}' is now on GitHub.")
        if args.github_username:
            print(f"View it at:https://github.com/{args.github_username}/{repo_name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mkghrepo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    api = subparsers.add_parser("api")
    api.add_argument("name", nargs="?", default=None)
    api.add_argument("-d", "--description", default="created with python")
    api.add_argument("--private", action="store_true")
    api.add_argument("--auto-init", action="store_true")
    api.add_argument("--push", action="store_true")
    api.add_argument("--token")
    api.add_argument("--env-file", default="~/.env")
    api.add_argument("--api-url", default="https://api.github.com/user/repos")
    api.add_argument("--remote", default="origin")
    api.add_argument("--protocol", choices=["https", "ssh"], default="ssh")
    api.add_argument("--branch", default="main")
    api.add_argument("--commit-message", default="Update files")
    api.add_argument("--git-user")
    api.add_argument("--git-email")
    api.add_argument("--pull-rebase", action="store_true")

    gh = subparsers.add_parser("gh")
    gh.add_argument("name", nargs="?", default=None)
    gh.add_argument("-d", "--description")
    gh.add_argument("--private", action="store_true")
    gh.add_argument("--source", default=".")
    gh.add_argument("--remote", default="origin")
    gh.add_argument("--branch", default="main")
    gh.add_argument("--commit-message")
    gh.add_argument("--git-user", default="i4147")
    gh.add_argument("--git-email", default="adnanonagh@gmail.com")
    gh.add_argument("--github-username", default="i4147")
    gh.add_argument("--protocol", choices=["https", "ssh"], default="https")
    gh.add_argument("--existing", choices=["ask", "merge", "new", "exit"], default="ask")
    add_bool_argument(gh, "copy-global-gitignore", True)
    add_bool_argument(gh, "create-readme", True)
    add_bool_argument(gh, "init", True)
    add_bool_argument(gh, "commit", True)
    add_bool_argument(gh, "push", True)
    add_bool_argument(gh, "pull-rebase", True)
    add_bool_argument(gh, "rename-branch", True)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "api":
        return cmd_api(args)
    if args.command == "gh":
        return cmd_gh(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
