#!/data/data/com.termux/files/usr/bin/python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python command-line tool with the following specification:

The tool generates `setup.py` files for Python projects based on each project's `pyproject.toml`. It must be runnable as a script with a Termux-style shebang line for Android (`/data/data/com.termux/files/usr/bin/env python3`) and should use only the standard library, targeting Python 3.11 or newer because it relies on the built-in `tomllib` module.

Command-line interface: the script accepts zero or more project directory names as positional arguments, a flag `-a` (or equivalent long form) that processes every project found under the current working directory, and a `--force` flag that permits overwriting existing `setup.py` files. With no arguments, it processes the current directory as a single project. Running `-a` together with named projects, or combining `--force` with specific projects, must work as described in the usage examples. Invalid or missing project paths should be reported without aborting the whole run.

Core behavior: for each project directory, read `pyproject.toml` and determine the PEP 517 build backend from the `[build-system]` table's `build-backend` key. Handle parsing errors gracefully (malformed TOML, missing file, missing or unreadable table) and record them as results rather than crashing. Classify the outcome into three categories:

1. Setuptools backend (for example `setuptools.build_meta` or variants that begin with `setuptools`): write a minimal `setup.py` that consists of a short docstring stating it is a compatibility shim whose metadata lives in `pyproject.toml`, an import of `setup` from `setuptools`, and a bare `setup()` call.
2. Any other identified non-setuptools backend (for example Hatchling, Flit, Poetry, Maturin, PDM, Meson): write a `setup.py` containing only an informational docstring explaining that the project uses a non-setuptools backend, that `pyproject.toml` is authoritative, and that the file is not a functional build script. Do not emit a setuptools shim in this case.
3. Backend undeterminable (no build-system table, no backend key, or empty value): write an informational docstring telling the reader to inspect `pyproject.toml` before choosing a build configuration.

Do not overwrite an existing `setup.py` unless `--force` is given; instead record it as skipped with an explanatory detail. Each project's result should be a small immutable record holding the project path, a status string, and an optional detail message. Use `pathlib` for all path handling and write files with UTF-8 encoding.

Concurrency: read backends and process projects concurrently using a thread pool from `concurrent.futures`, collecting results and then printing a summary. Keep file writes deterministic and avoid race conditions between projects. Use `os` where needed for directory scanning, and `sys` for exit codes and stderr messages.

Discovery with `-a`: scan immediate subdirectories of the current directory and include those that contain a `pyproject.toml`; ignore hidden directories and ones without that file. Print a concise per-project status line and a final count summary, and exit with a nonzero code if any project errored (but not merely for skips).

Output requirements: include a module docstring with the usage examples, `from __future__ import annotations` at the top, type hints throughout, and a `main()` function guarded by `if __name__ == "__main__":`. Keep the code clean, idiomatic, and consistent in naming and comment density with the rest of the project. Provide the complete file as the deliverable.
---"""

#!/data/data/com.termux/files/usr/bin/env python3
"""Generate setup.py files from Python project configurations.

Usage:
    python gen_setup.py
    python gen_setup.py project_a project_b
    python gen_setup.py -a
    python gen_setup.py -a --force project_a

Setuptools projects receive a minimal setup() shim.
Non-setuptools projects receive a clearly marked compatibility notice
instead of an incompatible setuptools shim.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import sys
import tomllib
from pathlib import Path
from typing import NamedTuple

SETUP_SHIM = '''"""Compatibility shim; project metadata is defined in pyproject.toml."""

from setuptools import setup

setup()
'''

NON_SETUP_NOTICE = '''"""This project uses a non-setuptools build backend.

See pyproject.toml for the authoritative build configuration.
This file is informational and is not a functional build script.
"""
'''

UNKNOWN_NOTICE = '''"""Build backend could not be determined automatically.

Inspect pyproject.toml before choosing a build configuration.
"""
'''

PYPROJECT_NAME = "pyproject.toml"
SETUP_NAME = "setup.py"


class Result(NamedTuple):
    project: Path
    status: str
    detail: str = ""


def read_backend(project: Path) -> tuple[str | None, str]:
    """Read the PEP 517 build backend and report parsing errors."""
    config = project / PYPROJECT_NAME

    if not config.is_file():
        return None, "missing pyproject.toml"

    try:
        with config.open("rb") as file:
            data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return None, f"cannot parse pyproject.toml: {exc}"

    build_system = data.get("build-system", {})
    backend = build_system.get("build-backend")

    if not isinstance(backend, str) or not backend.strip():
        return None, "build-system.build-backend is missing"

    return backend.strip(), ""


def discover_projects(paths: list[Path]) -> list[Path]:
    """Find project roots without descending into common generated directories."""
    excluded = {
        ".git",
        ".hg",
        ".svn",
        ".tox",
        ".venv",
        "venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        ".nox",
        ".mypy_cache",
        ".pytest_cache",
    }
    found: set[Path] = set()

    for path in paths:
        path = path.expanduser()

        if path.is_file():
            if path.name == PYPROJECT_NAME:
                found.add(path.parent.resolve())
            elif path.name == SETUP_NAME:
                found.add(path.parent.resolve())
            else:
                print(f"SKIP {path}: not a project directory or config file")
            continue

        if not path.is_dir():
            print(f"SKIP {path}: path does not exist")
            continue

        path = path.resolve()

        if (path / PYPROJECT_NAME).is_file():
            found.add(path)
            continue

        for root, dirs, files in os.walk(path):
            dirs[:] = sorted(d for d in dirs if d not in excluded)
            root_path = Path(root)

            if PYPROJECT_NAME in files:
                found.add(root_path)
                dirs[:] = []

    return sorted(found)


def classify(backend: str | None) -> tuple[str, str]:
    """Return output content and classification."""
    if backend == "setuptools.build_meta" or (backend and backend.startswith("setuptools.build_meta:")):
        return SETUP_SHIM, "setuptools"

    if backend:
        return NON_SETUP_NOTICE, f"non-setuptools backend: {backend}"

    return UNKNOWN_NOTICE, "unknown backend"


def process_project(
    project: Path,
    apply: bool,
    force: bool,
) -> Result:
    backend, error = read_backend(project)

    if error:
        return Result(project, "SKIP", error)

    content, classification = classify(backend)
    target = project / SETUP_NAME

    if target.exists() and not force:
        return Result(project, "EXISTS", "use --force to replace")

    if not apply:
        action = "CREATE" if not target.exists() else "REPLACE"
        return Result(project, action, classification)

    try:
        # Exclusive creation avoids overwriting a file created concurrently.
        if target.exists() and force:
            target.write_text(content, encoding="utf-8")
        else:
            with target.open("x", encoding="utf-8", newline="\n") as file:
                file.write(content)
    except FileExistsError:
        return Result(project, "EXISTS", "file appeared during generation")
    except OSError as exc:
        return Result(project, "ERROR", str(exc))

    return Result(project, "WROTE", classification)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate setup.py compatibility files for Python projects.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="project directories or pyproject.toml files",
    )
    parser.add_argument(
        "-a",
        "--apply",
        action="store_true",
        help="write files (default: dry-run)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace existing setup.py files; requires --apply",
    )
    parser.add_argument(
        "-j",
        "--workers",
        type=int,
        default=min(8, os.cpu_count() or 1),
        help="worker count (default: up to 8)",
    )
    args = parser.parse_args()

    if args.force and not args.apply:
        parser.error("--force requires --apply")
    if args.workers < 1:
        parser.error("--workers must be at least 1")

    roots = args.paths or [Path.cwd()]
    projects = discover_projects(roots)

    if not projects:
        print("No projects containing pyproject.toml were found.")
        return 1

    counts: dict[str, int] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_project, project, args.apply, args.force) for project in projects]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            counts[result.status] = counts.get(result.status, 0) + 1
            suffix = f" — {result.detail}" if result.detail else ""
            print(f"{result.status:8} {result.project / SETUP_NAME}{suffix}")

    print("\nSummary:")
    print(f"  Projects found: {len(projects)}")
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")
    print(f"  Mode: {'WRITE' if args.apply else 'DRY-RUN'}")

    return 0 if not counts.get("ERROR") and not counts.get("SKIP") else 1


if __name__ == "__main__":
    raise SystemExit(main())
