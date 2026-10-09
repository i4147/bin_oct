#!/data/data/com.termux/files/usr/bin/python
"""Unified GitHub clone/download tool.

Subcommands:
  clone  Shallow clone through a selectable backend (from g1.py).
  bare   Bare single-branch clone with submodules (from gitclone.py).
  zip    Download a repository ZIP archive (from ghzip.py, gitzip.py, ziprepo.py).

Examples:
  python merged.py clone owner/repo
  python merged.py clone https://github.com/owner/repo -b dulwich --token TOKEN
  python merged.py bare https://github.com/owner/repo [target-dir]
  python merged.py zip owner/repo
  python merged.py zip owner/repo -b urllib --no-size-check --filename-template "{repo}.zip" --env-file ""
  python merged.py zip owner/repo -b pygithub --branch main --require-token --verbose-output
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Callable, Optional, Sequence
from urllib.parse import urlparse

from loguru import logger

SSH_PREFIX = "git@github.com:"
URL_PREFIXES = ("http://", "https://")
GITMODULES = ".gitmodules"
CLONE_BACKENDS = ("gh", "git", "dulwich", "gitpython", "libgit2", "typer")
ZIP_BACKENDS = ("subprocess", "pygithub", "gitpython", "dulwich", "typer", "urllib")
DEFAULT_ENV_FILE = str(Path.home() / ".env")
DEFAULT_CLONE_SIZE_MB = 50
DEFAULT_ZIP_SIZE_BYTES = 5242880
DEFAULT_FALLBACK_BRANCH = "master"
DEFAULT_ZIP_TEMPLATE = "{repo}-{branch}.zip"


def run(cmd: Sequence[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    logger.debug(f"Running: {' '.join(cmd)} (cwd={cwd})")
    return subprocess.run(list(cmd), cwd=str(cwd) if cwd else None, check=check, capture_output=True, text=True)


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def parse_repo(spec: str) -> tuple[str, str]:
    spec = spec.strip().rstrip("/").removesuffix(".git")
    if spec.startswith(SSH_PREFIX):
        spec = spec[len(SSH_PREFIX) :]
    elif spec.startswith(URL_PREFIXES):
        spec = urlparse(spec).path
    parts = [p for p in spec.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"Invalid repository format: {spec}")
    return parts[0], parts[1]


class CloneBackend:
    name = ""

    def clone(self, url: str, target: Path, branch: str, depth: Optional[int] = 1) -> None:
        raise NotImplementedError

    def update_submodules(self, path: Path) -> None:
        raise NotImplementedError


class SubprocessBackend(CloneBackend):
    def __init__(self, name: str, prefer_gh: bool = True) -> None:
        self.name = name
        self.prefer_gh = prefer_gh and have("gh")

    def clone(self, url: str, target: Path, branch: str, depth: Optional[int] = 1) -> None:
        if target.exists() and any(target.iterdir()):
            raise Exception(f"Target directory already exists and is not empty: {target}")
        if self.prefer_gh:
            cmd = ["gh", "repo", "clone", url, str(target), "--", "--branch", branch]
            if depth is not None:
                cmd.extend(["--depth", str(depth)])
            try:
                run(cmd)
                return
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.warning(f"gh clone failed, falling back to git: {e}")
        if not have("git"):
            raise Exception("Neither 'gh' nor 'git' is available on PATH.")
        cmd = ["git", "clone", url, str(target), "--branch", branch]
        if depth is not None:
            cmd.extend(["--depth", str(depth)])
        run(cmd)

    def update_submodules(self, path: Path) -> None:
        git_submodule_update(path)


class DulwichBackend(CloneBackend):
    name = "dulwich"

    def clone(self, url: str, target: Path, branch: str, depth: Optional[int] = 1) -> None:
        from dulwich import porcelain

        porcelain.clone(source=url, target=str(target), branch=branch.encode("utf-8"), depth=depth)

    def update_submodules(self, path: Path) -> None:
        from dulwich import porcelain

        porcelain.submodule_update(root=str(path), recursive=True)


class GitPythonBackend(CloneBackend):
    name = "gitpython"

    def clone(self, url: str, target: Path, branch: str, depth: Optional[int] = 1) -> None:
        from git import Repo

        kwargs: dict = {"branch": branch}
        if depth is not None:
            kwargs["depth"] = depth
            kwargs["single_branch"] = True
        Repo.clone_from(url, str(target), **kwargs)

    def update_submodules(self, path: Path) -> None:
        from git import Repo

        for submodule in Repo(str(path)).submodules:
            submodule.update(init=True, recursive=True)


class Libgit2Backend(CloneBackend):
    name = "libgit2"

    def clone(self, url: str, target: Path, branch: str, depth: Optional[int] = 1) -> None:
        if depth is not None:
            raise NotImplementedError("pygit2/libgit2 does not support shallow clones; falling back to subprocess git.")
        import pygit2

        pygit2.clone_repository(url, str(target), checkout_branch=branch)

    def update_submodules(self, path: Path) -> None:
        raise NotImplementedError("pygit2 does not expose recursive submodule update; falling back to subprocess git.")


class TyperBackend(CloneBackend):
    name = "typer"

    def __init__(self) -> None:
        self._fallback = SubprocessBackend("git", prefer_gh=False)

    def clone(self, url: str, target: Path, branch: str, depth: Optional[int] = 1) -> None:
        self._fallback.clone(url, target, branch, depth)

    def update_submodules(self, path: Path) -> None:
        self._fallback.update_submodules(path)


def make_clone_backend(name: str) -> CloneBackend:
    name = name.lower()
    if name in ("gh", "git"):
        return SubprocessBackend(name, prefer_gh=(name == "gh"))
    factories: dict[str, Callable[[], CloneBackend]] = {
        "dulwich": DulwichBackend,
        "gitpython": GitPythonBackend,
        "libgit2": Libgit2Backend,
        "typer": TyperBackend,
    }
    if name not in factories:
        raise ValueError(f"Unknown backend: {name}")
    return factories[name]()


def git_submodule_update(path: Path) -> None:
    if not have("git"):
        raise Exception("'git' is not available for submodule update.")
    try:
        run(["git", "submodule", "update", "--init", "--recursive"], cwd=path)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Submodule update failed in {path}: {e.stderr or e}")


def has_submodules(path: Path) -> bool:
    if (path / GITMODULES).is_file():
        return True
    try:
        for found in path.rglob(GITMODULES):
            if found.is_file():
                return True
    except OSError as e:
        logger.warning(f"Error scanning for submodules: {e}")
    return False


def update_all_submodules(root: Path, backend: CloneBackend) -> None:
    seen: set[Path] = set()
    stack = [root]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        if not has_submodules(current):
            continue
        print(f"Updating submodules in {current}...")
        try:
            backend.update_submodules(current)
            print(f"Submodules updated in {current} via {backend.name}.")
        except NotImplementedError as e:
            logger.warning(f"Backend '{backend.name}' cannot update submodules: {e}. Using subprocess git.")
            git_submodule_update(current)
            print(f"Submodules updated in {current} via fallback git.")
        except Exception as e:
            logger.warning(f"Backend '{backend.name}' submodule update failed: {e}. Trying subprocess git.")
            try:
                git_submodule_update(current)
                print(f"Submodules updated in {current} via fallback git.")
            except Exception as e2:
                raise Exception(f"Submodule update failed in {current}: {e2}")
        for child in current.iterdir():
            if not child.is_dir() or child in seen:
                continue
            if has_submodules(child):
                stack.append(child)


def prompt_submodules(path: Path, backend: CloneBackend) -> None:
    if not has_submodules(path):
        print("No submodules found.")
        return
    print("Submodules found. Initialize and update? (y/n)")
    if input().lower() != "y":
        print("Submodule initialization skipped.")
        return
    try:
        update_all_submodules(path, backend)
    except Exception as e:
        raise Exception(f"Submodule update failed: {e}")


def fetch_repo(spec: str, client):
    from github.GithubException import GithubException, UnknownObjectException

    try:
        owner, name = parse_repo(spec)
        print(f"Fetching repository: {owner}/{name}")
        repo = client.get_user(owner).get_repo(name)
        _ = repo.size  # touch a lazy attribute so a missing repo fails here
        print(f"Repository found: {repo.full_name}")
        return repo
    except UnknownObjectException:
        raise ValueError(f"Repository not found: {spec}")
    except GithubException as e:
        raise Exception(f"GitHub API error: {e.status} {e.data}")


def repo_size_mb(repo) -> float:
    try:
        size_mb = repo.size / 1024
        print(f"Repository size: {size_mb:.2f} MB")
        return size_mb
    except Exception as e:
        logger.error(f"Could not fetch repo size: {e}")
        return 0.0


def default_branch(repo) -> str:
    try:
        branch = repo.default_branch
        print(f"Default branch: {branch}")
        return branch
    except Exception as e:
        logger.warning(f"Could not determine default branch: {e}")
        return "main"


def confirm_clone_size(size_mb: float, limit_mb: float) -> bool:
    if size_mb > limit_mb:
        logger.warning(f"Repository size is {size_mb:.2f} MB. Continue? (y/n)")
        return input().lower() == "y"
    return True


def clone_target(url: str) -> Path:
    return Path.cwd() / Path(url.rstrip("/").removesuffix(".git")).name


def clone_repo(url: str, branch: str, backend: CloneBackend, depth: Optional[int]) -> Path:
    depth_label = f"depth={depth}" if depth is not None else "full history"
    print(f"Cloning repository from {url} (branch: {branch}, {depth_label}, backend: {backend.name})")
    target = clone_target(url)
    try:
        backend.clone(url, target, branch, depth)
        print(f"Clone completed successfully at {target}.")
        return target
    except NotImplementedError as e:
        logger.warning(f"Backend '{backend.name}' cannot clone shallow: {e}")
    except Exception as e:
        logger.warning(f"Backend '{backend.name}' clone failed: {e}")
    if not have("git"):
        raise Exception(f"Backend '{backend.name}' failed and 'git' is not available for fallback.")
    logger.info("Falling back to subprocess git for clone.")
    try:
        SubprocessBackend("git", prefer_gh=False).clone(url, target, branch, depth)
        print(f"Clone completed via fallback git at {target}.")
        return target
    except Exception as e:
        raise Exception(f"[ERROR] Clone failed: {e}")


def cmd_clone(args: argparse.Namespace) -> int:
    from github import Github
    from github.GithubException import GithubException

    spec = args.repository_url.strip()
    token = args.token
    depth = args.depth if args.depth and args.depth > 0 else None
    try:
        backend = make_clone_backend(args.backend)
    except ValueError as e:
        logger.error(f"{e}")
        return 1
    print(f"Using backend: {backend.name}")
    try:
        client = Github(token) if token else Github()
        if token:
            print(f"Authenticated as: {client.get_user().login}")
    except GithubException as e:
        logger.error(f"Authentication failed: {e}")
        return 1
    try:
        repo = fetch_repo(spec, client)
    except Exception as e:
        logger.error(f"{e}")
        return 1
    if not confirm_clone_size(repo_size_mb(repo), args.size_limit_mb):
        print("Aborted by user.")
        return 0
    branch = default_branch(repo)
    url = repo.clone_url
    try:
        target = clone_repo(url, branch, backend, depth)
    except Exception as e:
        if "not found" in str(e).lower() or "fatal:" in str(e):
            # retry with the conventional alternate when the detected branch is missing
            alt = args.fallback_branch if branch == "main" else "main"
            logger.warning(f"Branch '{branch}' failed, trying '{alt}'...")
            try:
                target = clone_repo(url, alt, backend, depth)
            except Exception as e2:
                logger.error(f"Clone with both branches failed: {e2}")
                return 1
        else:
            logger.error(f"{e}")
            return 1
    try:
        prompt_submodules(target, backend)
    except Exception as e:
        logger.warning(f"Submodule handling failed: {e}")
    return 0


def detect_remote_default_branch(url: str) -> Optional[str]:
    result = subprocess.run(["git", "ls-remote", "--symref", url, "HEAD"], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        match = re.match(r"^ref:\s+refs/heads/(\S+)\s+HEAD", line)
        if match:
            return match.group(1)
    return None


def repo_has_gitmodules(path: Path) -> bool:
    return (
        subprocess.run(["git", "-C", str(path), "cat-file", "-e", f"HEAD:{GITMODULES}"], capture_output=True).returncode
        == 0
    )


def cmd_bare(args: argparse.Namespace) -> int:
    url = args.url
    branch = detect_remote_default_branch(url)
    if not branch:
        print(f"❌ Could not determine default branch for {url}", file=sys.stderr)
        return 1
    target = args.target
    if not target:
        name = Path(url.rstrip("/")).name.removesuffix(".git")
        target = f"{name}{args.suffix}"
    print(f"🔍 Default branch: {branch}")
    print(f"📦 Cloning only '{branch}' (with submodules) from {url} into {target} ...")
    code = subprocess.run([
        "git",
        "clone",
        "--single-branch",
        "--branch",
        branch,
        "--bare",
        "--recurse-submodules",
        url,
        target,
    ]).returncode
    if code != 0:
        return code
    submodules = repo_has_gitmodules(Path(target))
    print("✅ Done!")
    print(f"   To update later: cd {target} && git fetch origin {branch}")
    if submodules:
        print("   Update submodules: git submodule update --init --recursive --remote")
    return 0


def resolve_token(env_file: str) -> Optional[str]:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    path = Path(env_file).expanduser() if env_file else None
    if path and path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(path)
            return os.environ.get("GITHUB_TOKEN")
        except Exception:
            pass
    return None


def gh_env(token: Optional[str]) -> dict:
    env = os.environ.copy()
    if token:
        env["GITHUB_TOKEN"] = token
    return env


def curl_header_args(token: Optional[str]) -> list[str]:
    headers = ["Accept: application/vnd.github+json", "X-GitHub-Api-Version: 2022-11-28"]
    if token:
        headers.append(f"Authorization: Bearer {token}")
    return [arg for header in headers for arg in ("-H", header)]


def urllib_headers(token: Optional[str], api: bool) -> dict:
    headers = {"User-Agent": "zip-downloader"}
    if api:
        headers["Accept"] = "application/vnd.github+json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def repo_field(owner: str, repo: str, token: Optional[str], field: str, use_urllib: bool) -> str:
    api = f"https://api.github.com/repos/{owner}/{repo}"
    if use_urllib:
        request = urllib.request.Request(api, headers=urllib_headers(token, api=True))
        with urllib.request.urlopen(request) as resp:
            return str(json.load(resp)[field])
    if have("gh"):
        return subprocess.check_output(["gh", "api", api, "--jq", f".{field}"], text=True, env=gh_env(token)).strip()
    curl = shutil.which("curl")
    if curl:
        out = subprocess.check_output([curl, "-fsSL", *curl_header_args(token), api], text=True)
        return str(json.loads(out)[field])
    raise RuntimeError("Neither gh nor curl is available for repo lookup")


def remote_size_bytes(owner: str, repo: str, token: Optional[str], use_urllib: bool) -> Optional[int]:
    try:
        return int(repo_field(owner, repo, token, "size", use_urllib)) * 1024
    except Exception:
        return None


def confirm_zip_size(size: Optional[int], limit: int) -> bool:
    if size is None or size < limit:
        return True
    prompt = f"Repo looks larger than {limit / 1048576:g} MB ({size / 1048576:.2f} MB). Download anyway? [y/N]: "
    try:
        if sys.stdin is not None and sys.stdin.isatty():
            return input(prompt).strip().lower() in {"y", "yes"}
    except Exception:
        pass
    return True


def fetch_url_to_file(url: str, dest: Path, headers: dict) -> None:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as resp, open(dest, "wb") as fh:
        shutil.copyfileobj(resp, fh)


def zip_via_subprocess(owner: str, repo: str, branch: str, dest: Path, token: Optional[str]) -> None:
    if have("gh"):
        cmd = ["gh", "api", f"/repos/{owner}/{repo}/zipball/{branch}", "-H", "Accept: application/vnd.github+json"]
        with open(dest, "wb") as fh:
            subprocess.run(cmd, check=True, env=gh_env(token), stdout=fh)
        return
    archive = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    auth = ["-H", f"Authorization: Bearer {token}"] if token else []
    if have("curl"):
        subprocess.run(["curl", "-fL", *auth, "-o", str(dest), archive], check=True, env=gh_env(token))
        return
    if have("wget"):
        subprocess.run(["wget", "-O", str(dest), archive], check=True, env=gh_env(token))
        return
    raise RuntimeError("No supported subprocess downloader found (gh/curl/wget)")


def zip_via_pygithub(owner: str, repo: str, branch: str, dest: Path, token: Optional[str]) -> bool:
    try:
        from github import Github
    except Exception:
        return False
    client = Github(token) if token else Github()
    link = client.get_repo(f"{owner}/{repo}").get_archive_link("zipball", ref=branch)
    headers = {"User-Agent": "python"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    fetch_url_to_file(link, dest, headers)
    return True


def zip_via_gitpython(owner: str, repo: str, branch: str, dest: Path, token: Optional[str]) -> bool:
    try:
        from git import Repo
    except Exception:
        return False
    tmp = Path.cwd() / f".tmp-{repo}-{branch}"
    if tmp.exists():
        shutil.rmtree(tmp)
    Repo.clone_from(f"https://github.com/{owner}/{repo}.git", tmp, branch=branch, depth=1)
    shutil.make_archive(str(dest.with_suffix("")), "zip", tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    return True


def zip_via_dulwich(owner: str, repo: str, branch: str, dest: Path, token: Optional[str]) -> bool:
    try:
        from dulwich import porcelain
    except Exception:
        return False
    tmp = Path.cwd() / f".tmp-{repo}-{branch}-dulwich"
    if tmp.exists():
        shutil.rmtree(tmp)
    porcelain.clone(f"https://github.com/{owner}/{repo}.git", str(tmp), checkout=True)
    shutil.make_archive(str(dest.with_suffix("")), "zip", tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    return True


def zip_via_urllib(owner: str, repo: str, branch: str, dest: Path, token: Optional[str]) -> bool:
    url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    fetch_url_to_file(url, dest, urllib_headers(token, api=False))
    return True


ZIP_HANDLERS: dict[str, Callable[[str, str, str, Path, Optional[str]], bool]] = {
    "pygithub": zip_via_pygithub,
    "gitpython": zip_via_gitpython,
    "dulwich": zip_via_dulwich,
    "urllib": zip_via_urllib,
}


def cmd_zip(args: argparse.Namespace) -> int:
    token = resolve_token(args.env_file)
    if args.require_token and not token:
        logger.error("❌ Error: GITHUB_TOKEN environment variable not set.")
        return 1
    try:
        owner, repo = parse_repo(args.repo)
    except ValueError as e:
        logger.error(f"❌ Error: {e}")
        return 1
    use_urllib = args.backend == "urllib"
    try:
        if not args.no_size_check:
            size = remote_size_bytes(owner, repo, token, use_urllib)
            if not confirm_zip_size(size, args.size_limit_bytes):
                print("Skipped by user choice.")
                return 0
        branch = args.branch
        if not branch:
            try:
                branch = repo_field(owner, repo, token, "default_branch", use_urllib)
            except Exception:
                branch = args.fallback_branch
        if args.output:
            dest = Path(args.output)
        else:
            dest = Path.cwd() / args.filename_template.format(owner=owner, repo=repo, branch=branch)
        if args.verbose_output:
            print(f"Connecting to repository: {owner}/{repo}...")
            print(f"Fetching zipball for branch: {branch}...")
        if dest.exists():
            dest.unlink()
        handler = ZIP_HANDLERS.get(args.backend)
        done = handler(owner, repo, branch, dest, token) if handler else False
        if not done:
            zip_via_subprocess(owner, repo, branch, dest, token)
        if args.verbose_output:
            size_bytes = dest.stat().st_size
            print(f"📦 Download size: {size_bytes / 1048576:.2f} MB ({size_bytes:,} bytes)")
            print(f"✅ Successfully downloaded: {dest.absolute()}")
        else:
            print(str(dest))
        return 0
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="merged.py",
        description="Clone or download GitHub repositories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    clone = sub.add_parser("clone", help="Shallow clone using a pluggable backend")
    clone.add_argument("repository_url", help="Repository identifier or URL (owner/repo, HTTPS, or SSH).")
    clone.add_argument("--token", default=None, help="GitHub personal access token (increases rate limit).")
    clone.add_argument("-b", "--backend", default="gh", choices=CLONE_BACKENDS, help="Clone backend. Default: gh.")
    clone.add_argument("--depth", type=int, default=1, help="Clone depth; 0 for full history. Default: 1.")
    clone.add_argument(
        "--size-limit-mb", type=float, default=DEFAULT_CLONE_SIZE_MB, help="Prompt above this size in MB. Default: 50."
    )
    clone.add_argument(
        "--fallback-branch",
        default=DEFAULT_FALLBACK_BRANCH,
        help="Retry branch when the default is 'main' and cloning fails. Default: master.",
    )
    clone.set_defaults(func=cmd_clone)

    bare = sub.add_parser("bare", help="Bare single-branch clone with submodules")
    bare.add_argument("url", help="Repository URL.")
    bare.add_argument("target", nargs="?", default="", help="Target directory (default: <name><suffix>).")
    bare.add_argument("--suffix", default=".git", help="Suffix for the default target directory. Default: .git.")
    bare.set_defaults(func=cmd_bare)

    zp = sub.add_parser("zip", help="Download a repository ZIP archive")
    zp.add_argument("repo", help="Repository in owner/repo or full GitHub URL form.")
    zp.add_argument(
        "-b", "--backend", default="subprocess", choices=ZIP_BACKENDS, help="Backend to use. Default: subprocess."
    )
    zp.add_argument("--branch", default=None, help="Branch to download (default: auto-detect default branch).")
    zp.add_argument(
        "--fallback-branch", default="main", help="Branch used if default-branch lookup fails. Default: main."
    )
    zp.add_argument("-o", "--output", default=None, help="Output file name (overrides --filename-template).")
    zp.add_argument(
        "--filename-template",
        default=DEFAULT_ZIP_TEMPLATE,
        help="Output name template using {owner}, {repo}, {branch}. Default: {repo}-{branch}.zip.",
    )
    zp.add_argument(
        "--env-file",
        default=DEFAULT_ENV_FILE,
        help="Dotenv file to load GITHUB_TOKEN from; empty string disables. Default: ~/.env.",
    )
    zp.add_argument(
        "--size-limit-bytes",
        type=int,
        default=DEFAULT_ZIP_SIZE_BYTES,
        help="Prompt at or above this size. Default: 5242880.",
    )
    zp.add_argument("--no-size-check", action="store_true", help="Skip the size lookup and prompt.")
    zp.add_argument("--require-token", action="store_true", help="Fail if GITHUB_TOKEN is not set.")
    zp.add_argument("--verbose-output", action="store_true", help="Print progress, download size and absolute path.")
    zp.set_defaults(func=cmd_zip)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
