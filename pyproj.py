#!/data/data/com.termux/files/home/.local/bin/python
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Final

from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

ENV_PATH: Final[Path] = Path.home() / ".env"
"""Location of the .env file that holds GITHUB_TOKEN."""

GITHUB_API: Final[str] = "https://api.github.com"
"""Base URL for the GitHub REST API."""

DEFAULT_BRANCH: Final[str] = "main"
"""Branch name used for the initial commit and remote tracking."""

VERSION: Final[str] = "1.4.7"
"""Version stamped into pyproject.toml, __init__.py, <pkgname>.py, <pkgname>.pyx."""

# Load .env early so GITHUB_TOKEN is available to any subsequent code.
load_dotenv(dotenv_path=ENV_PATH)

# --------------------------------------------------------------------------- #
# File templates -- shared
# --------------------------------------------------------------------------- #

GITIGNORE: Final[str] = """\
__pycache__/
*.py[codz]
*$py.class
*.so
build/
dist/
eggs/
.eggs/
*.egg-info/
*.egg
MANIFEST
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
coverage.xml
.hypothesis/
.pytest_cache/
.env
.envrc
.venv
uv.lock
.ruff_cache/
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/
.pytype/
site/
"""

# setup.py is a minimal shim: all metadata lives in pyproject.toml.
# It exists for tools / workflows that still expect a setup.py to be present.
# NOTE: the Cython layout uses a *different* setup.py (see
# SETUP_PY_CYTHON_TMPL below) because it must declare ``ext_modules``.
SETUP_PY: Final[str] = '''\
"""Legacy shim for tools that still expect a setup.py.

All project metadata lives in pyproject.toml and setup.cfg.
"""

from setuptools import setup

setup()
'''

# --------------------------------------------------------------------------- #
# File templates -- package layout
#
# The src-layout package contains only two modules:
#   * __init__.py -- package version marker
#   * cli.py      -- Typer application and console entry point
# All other helpers (credentials, logging, utils, __main__, py.typed) were
# intentionally dropped: they can be added back by the user on demand.
# --------------------------------------------------------------------------- #

PYPROJECT_PKG_TMPL: Final[str] = """\
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "{pkgname}"
version = "{version}"
readme = "README.md"
authors = [
  {{name = "isaac onagh", email = "mkalafsaz@gmail.com"}}
]
requires-python = ">= 3.12"

[project.scripts]
{pkgname} = "{pkgname}.cli:main"
"""

SETUP_CFG_PKG_TMPL: Final[str] = """\
[options]
package_dir =
    = src
packages = find:
python_requires = >= 3.12

[options.packages.find]
where = src


[mypy]
python_version = 3.12
strict = True
warn_unused_ignores = True
warn_redundant_casts = True
warn_unreachable = True
files = src

[ruff]
line-length = 120
target-version = py312

[tool:pytest]
testpaths = tests
addopts = -ra -q
"""

INIT_PY_TMPL: Final[str] = '__version__ = "{version}"\n'

CLI_PY_TMPL: Final[str] = """\
import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def main() -> None:
    console.print(
        "Replace this message by putting your code into {pkgname}.cli.main"
    )


if __name__ == "__main__":
    app()
"""

# --------------------------------------------------------------------------- #
# File templates -- single-file layout
# --------------------------------------------------------------------------- #

PYPROJECT_SINGLE_TMPL: Final[str] = """\
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "{pkgname}"
version = "{version}"
readme = "README.md"
authors = [
  {{name = "isaac onagh", email = "mkalafsaz@gmail.com"}}
]
requires-python = ">= 3.12"

[project.scripts]
{pkgname} = "{pkgname}:main"
"""

SETUP_CFG_SINGLE_TMPL: Final[str] = """\
[options]
py_modules = {pkgname}
python_requires = >= 3.12
install_requires =

[mypy]
python_version = 3.12
strict = True
warn_unused_ignores = True
warn_redundant_casts = True
warn_unreachable = True
files = {pkgname}.py

[ruff]
line-length = 120
target-version = py312

[tool:pytest]
testpaths = tests
addopts = -ra -q
"""

SINGLE_FILE_PY_TMPL: Final[str] = '''\
"""{pkgname} -- a single-file Python module."""

from __future__ import annotations

__version__ = "{version}"


def main() -> None:
    """Console-script entry point for the ``{pkgname}`` command."""
    print("Hello from {pkgname}")


if __name__ == "__main__":
    main()
'''

# --------------------------------------------------------------------------- #
# File templates -- Cython layout
#
# A Cython project is a *single extension module* named <pkgname> built from
# one <pkgname>.pyx source file at the project root. It looks like the
# single-file layout from the user's point of view, but differs in two ways:
#
#   1. build-system requires "Cython" in addition to "setuptools".
#   2. setup.py is *required* (not a legacy shim) because setuptools must be
#      told about the Extension via ``ext_modules`` -- there is no
#      declarative equivalent in pyproject.toml / setup.cfg.
# --------------------------------------------------------------------------- #

PYPROJECT_CYTHON_TMPL: Final[str] = """\
[build-system]
requires = ["setuptools", "Cython"]
build-backend = "setuptools.build_meta"

[project]
name = "{pkgname}"
version = "{version}"
readme = "README.md"
authors = [
  {{name = "isaac onagh", email = "mkalafsaz@gmail.com"}}
]
requires-python = ">= 3.12"

[project.scripts]
{pkgname} = "{pkgname}:main"
"""

SETUP_CFG_CYTHON_TMPL: Final[str] = """\
[options]
python_requires = >= 3.12
install_requires =

[ruff]
line-length = 120
target-version = py312

[tool:pytest]
testpaths = tests
addopts = -ra -q
"""

# Required (unlike the other layouts): setuptools needs ``ext_modules``,
# which cannot be expressed declaratively in pyproject.toml / setup.cfg.
SETUP_PY_CYTHON_TMPL: Final[str] = '''\
"""Build configuration for the Cython extension module ``{pkgname}``.

Unlike the pure-Python layouts, this file is *required*: setuptools must be
told about the C extension via ``ext_modules``, which has no declarative
equivalent in ``pyproject.toml`` / ``setup.cfg``. All other project metadata
still lives in ``pyproject.toml`` and ``setup.cfg``.
"""

from setuptools import Extension, setup
from Cython.Build import cythonize

# ``Extension("<name>", ["<src>"])`` builds ``{pkgname}`` from the single
# Cython source file ``{pkgname}.pyx`` at the project root. Language level 3
# is the recommended default for Python 3-only code.
extensions = [
    Extension("{pkgname}", ["{pkgname}.pyx"]),
]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={{"language_level": "3"}},
    ),
)
'''

CYTHON_PYX_TMPL: Final[str] = '''\
# cython: language_level=3
"""{pkgname} -- a Cython extension module."""

__version__ = "{version}"


def main() -> None:
    """Console-script entry point for the ``{pkgname}`` command."""
    print("Hello from {pkgname}")
'''

# --------------------------------------------------------------------------- #
# Shell helpers
# --------------------------------------------------------------------------- #


def run(cmd: list[str], cwd: Path) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


# --------------------------------------------------------------------------- #
# GitHub REST API helpers
# --------------------------------------------------------------------------- #


def github_request(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: bytes | None = json.dumps(payload).encode() if payload is not None else None

    req: urllib.request.Request = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            body: str = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail: str = e.read().decode(errors="replace")
        raise SystemExit(
            f"GitHub API error {e.code} on {method} {url}:\n{detail}"
        ) from e


def get_github_token() -> str:
    token: str | None = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit(
            f"GITHUB_TOKEN not found. Add it to {ENV_PATH}, e.g.\n"
            f"    GITHUB_TOKEN=ghp_xxx"
        )
    return token


def get_github_user(token: str) -> str:
    data: dict[str, Any] = github_request("GET", f"{GITHUB_API}/user", token)
    return str(data["login"])


def create_github_repo(
    token: str,
    name: str,
    *,
    private: bool = True,
    description: str = "",
) -> dict[str, Any]:
    return github_request(
        "POST",
        f"{GITHUB_API}/user/repos",
        token,
        {
            "name": name,
            "private": private,
            "description": description,
            "auto_init": False,
        },
    )


def get_or_create_github_repo(
    token: str,
    user: str,
    name: str,
    *,
    private: bool = True,
) -> dict[str, Any]:
    try:
        return github_request("GET", f"{GITHUB_API}/repos/{user}/{name}", token)
    except SystemExit as exc:
        # 404 means "not found" -> fall through to creation.
        if "404" not in str(exc):
            raise
    print(f"Repo {user}/{name} not found, creating ...")
    return create_github_repo(token, name, private=private)


# --------------------------------------------------------------------------- #
# Project scaffolding
# --------------------------------------------------------------------------- #


def render_package_files(pkgname: str) -> dict[Path, str]:
    src_pkg: Path = Path("src") / pkgname
    return {
        Path(".gitignore"): GITIGNORE,
        Path("README.md"): f"# {pkgname}\n",
        Path("pyproject.toml"): PYPROJECT_PKG_TMPL.format(
            pkgname=pkgname, version=VERSION
        ),
        Path("setup.py"): SETUP_PY,
        Path("setup.cfg"): SETUP_CFG_PKG_TMPL,
        src_pkg / "__init__.py": INIT_PY_TMPL.format(version=VERSION),
        src_pkg / "cli.py": CLI_PY_TMPL.format(pkgname=pkgname),
    }


def render_single_file_files(pkgname: str) -> dict[Path, str]:
    return {
        Path(".gitignore"): GITIGNORE,
        Path("README.md"): f"# {pkgname}\n",
        Path("pyproject.toml"): PYPROJECT_SINGLE_TMPL.format(
            pkgname=pkgname, version=VERSION
        ),
        Path("setup.py"): SETUP_PY,
        Path("setup.cfg"): SETUP_CFG_SINGLE_TMPL.format(pkgname=pkgname),
        Path(f"{pkgname}.py"): SINGLE_FILE_PY_TMPL.format(
            pkgname=pkgname, version=VERSION
        ),
    }


def render_cython_files(pkgname: str) -> dict[Path, str]:
    return {
        Path(".gitignore"): GITIGNORE,
        Path("README.md"): f"# {pkgname}\n",
        Path("pyproject.toml"): PYPROJECT_CYTHON_TMPL.format(
            pkgname=pkgname, version=VERSION
        ),
        Path("setup.py"): SETUP_PY_CYTHON_TMPL.format(pkgname=pkgname),
        Path("setup.cfg"): SETUP_CFG_CYTHON_TMPL,
        Path(f"{pkgname}.pyx"): CYTHON_PYX_TMPL.format(
            pkgname=pkgname, version=VERSION
        ),
    }


# Layout identifiers accepted by ``init_project``. ``layout`` is a plain
# string rather than a bool pair because the three options are mutually
# exclusive (enforced at the argparse layer) and a string keeps the dispatch
# table explicit.
LAYOUT_PACKAGE: Final[str] = "package"
LAYOUT_SINGLE: Final[str] = "single"
LAYOUT_CYTHON: Final[str] = "cython"


def init_project(pkgname: str, *, layout: str) -> tuple[Path, list[Path], list[Path]]:
    root: Path = Path.cwd() / pkgname
    root.mkdir(parents=True, exist_ok=True)

    if layout == LAYOUT_CYTHON:
        files: dict[Path, str] = render_cython_files(pkgname)
    elif layout == LAYOUT_SINGLE:
        files = render_single_file_files(pkgname)
    elif layout == LAYOUT_PACKAGE:
        files = render_package_files(pkgname)
    else:
        raise ValueError(f"Unknown layout: {layout!r}")

    created: list[Path] = []
    skipped: list[Path] = []

    for rel_path, content in files.items():
        abs_path: Path = root / rel_path
        # Create parent directories as needed; never remove existing ones.
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        if abs_path.exists():
            skipped.append(abs_path)
            continue

        abs_path.write_text(content, encoding="utf-8")
        created.append(abs_path)

    return root, created, skipped


# --------------------------------------------------------------------------- #
# Git operations
# --------------------------------------------------------------------------- #


def git_init_and_push(root: Path, remote_url: str) -> None:
    run(["git", "init", "-b", DEFAULT_BRANCH], cwd=root)
    run(["git", "add", "."], cwd=root)

    # Commit may be a no-op if there is nothing staged (e.g. re-run on an
    # unchanged repo). Use ``--allow-empty`` so the flow keeps moving.
    run(
        ["git", "commit", "--allow-empty", "-m", "Initial commit"],
        cwd=root,
    )

    # Replace or add ``origin``. ``git remote set-url`` fails if the remote
    # doesn't exist; check first.
    existing = subprocess.run(
        ["git", "remote"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()

    if "origin" in existing:
        run(["git", "remote", "set-url", "origin", remote_url], cwd=root)
    else:
        run(["git", "remote", "add", "origin", remote_url], cwd=root)

    run(["git", "push", "-u", "origin", DEFAULT_BRANCH], cwd=root)


def scrub_remote_token(root: Path, user: str, pkgname: str) -> None:
    clean_url: str = f"https://github.com/{user}/{pkgname}.git"
    run(["git", "remote", "set-url", "origin", clean_url], cwd=root)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).name,
        description=(
            "Scaffold a new Python project. Choose the default src-layout "
            "package, a single-file module (-s), or a Cython extension "
            "module (-c). With -g, also create a GitHub repo and push the "
            "initial commit. Existing files are never overwritten."
        ),
    )
    parser.add_argument(
        "pkgname",
        help="Python package / module name (also used as the directory name)",
    )

    # Layout selection: exactly one of the three layouts is allowed, and the
    # two single-module variants cannot be combined.
    layout_group = parser.add_mutually_exclusive_group()
    layout_group.add_argument(
        "-s",
        "--single-file",
        action="store_true",
        dest="single_file",
        help=(
            "Create a single-file module (<pkgname>.py) instead of the "
            "default src-layout package"
        ),
    )
    layout_group.add_argument(
        "-c",
        "--cython",
        action="store_true",
        dest="cython",
        help=(
            "Create a Cython extension module (<pkgname>.pyx) with a "
            "build-enabled setup.py. Mutually exclusive with -s."
        ),
    )

    parser.add_argument(
        "-g",
        "--git",
        action="store_true",
        dest="git",
        help=(
            "Also perform git init / commit / push and create the GitHub "
            "repository. When omitted, only the local project is scaffolded."
        ),
    )
    return parser.parse_args(argv)


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #


def main() -> None:
    args: argparse.Namespace = parse_args(sys.argv[1:])
    pkgname: str = args.pkgname
    single_file: bool = args.single_file
    cython: bool = args.cython
    do_git: bool = args.git

    if not pkgname.isidentifier():
        raise SystemExit(f"Error: {pkgname!r} is not a valid Python identifier")

    # Mutually exclusive group guarantees at most one of these is True.
    if cython:
        layout: str = LAYOUT_CYTHON
        layout_desc: str = "Cython extension module"
    elif single_file:
        layout = LAYOUT_SINGLE
        layout_desc = "single-file module"
    else:
        layout = LAYOUT_PACKAGE
        layout_desc = "src-layout package"

    print(f"Scaffolding {layout_desc} for {pkgname!r}")

    # 1. Scaffold the local project (only creating missing files).
    root, created, skipped = init_project(pkgname, layout=layout)
    print(f"Project root: {root}")
    print(f"  created: {len(created)} file(s)")
    for path in created:
        print(f"    + {path.relative_to(root)}")
    if skipped:
        print(f"  skipped (already exist): {len(skipped)} file(s)")
        for path in skipped:
            print(f"    = {path.relative_to(root)}")

    # If -g was not passed, stop here: nothing remote, nothing git.
    if not do_git:
        print(
            f"\nSkipping git init / commit / push and GitHub repo creation "
            f"(pass -g to enable).\nLocal project ready at {root}"
        )
        return

    # 2. Authenticate against GitHub.
    token: str = get_github_token()
    user: str = get_github_user(token)
    print(f"Authenticated as GitHub user: {user}")

    # 3. Fetch or create the remote repository.
    get_or_create_github_repo(token, user, pkgname, private=True)

    # 4. Initialise git and push using a token-embedded URL.
    push_url: str = f"https://{token}@github.com/{user}/{pkgname}.git"
    git_init_and_push(root, push_url)

    # 5. Immediately rewrite origin so the token does not persist on disk.
    scrub_remote_token(root, user, pkgname)

    print(f"\nDone: https://github.com/{user}/{pkgname}")


if __name__ == "__main__":
    main()
