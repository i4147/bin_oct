#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python 3.12 command-line script designed to run under Termux on Android (shebang: `/data/data/com.termux/files/usr/bin/python3.12`) that checks a Python `requirements.txt`-style file (in `pip freeze` format) against PyPI to find packages that have newer versions available.

Purpose and behavior:
- Accept command-line arguments (via `argparse`) for an input file path (default `requirements.txt`) and an output file path (default `upgradable.txt`), plus any other reasonable options (e.g., number of worker threads/timeout overrides).
- Parse the input file line by line:
  - Skip blank lines and comment lines (starting with `#`).
  - Skip editable installs (lines starting with `-e` or `--editable`).
  - Skip lines containing `@` (e.g., VCS/URL-based requirements).
  - Only process lines in the exact `name==version` pinned format; extract the package name and installed version into a dictionary.
- For each installed package, query the PyPI JSON API (`https://pypi.org/pypi/{name}/json`) to fetch the latest published version:
  - Use a shared `requests.Session` with a reasonable timeout (around 10 seconds).
  - Treat HTTP 404 as " package rather than raising).
  - Gracefully handle request exceptions, missing JSON keys, or malformed JSON by returning `None` for that package instead of crashing.
- Fetch latest versions concurrently using a `ThreadPoolExecutor` (e.g., up to 16 worker threads) to speed up checking many packages at once, collecting results via `as_completed`.
- Use the `packaging.version.Version` class to properly compare installed vs. latest versions (handling `InvalidVersion` exceptions gracefully, e.g., skipping or treating as not comparable rather than crashing on non-PEP440 versions).
- Determine which packages have a newer version available on PyPI compared to the installed version.
- Print a human-readable, colorized report to the terminal using ANSI escape codes (e.g., dimmed text for context/installed version, green for the available upgrade), clearly showing package name, installed version, and latest available version for each upgradable package.
- Write the list of upgradable packages (e.g., in `name==latest_version` format or similar) to the specified output file.
- Handle the case where the input file does not exist or cannot be read, printing an appropriate error message and exiting with a non-zero status code via `sys.exit`.
- Keep the script self-contained, using only `argparse`, `re`, `sys`, `pathlib.Path`, `concurrent.futures`, `requests`, and `packaging.version` as dependencies, with module-level constants (timeout, max workers, default input/output filenames, ANSI color codes, and a compiled regex for detecting editable install lines).
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/6vmywQ2B5RmSbupwTpVL5p"""

from __future__ import annotations
import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Final
import requests
from packaging.version import InvalidVersion, Version

_TIMEOUT: Final[float] = 10.0
_MAX_WORKERS: Final[int] = 16
_DEFAULT_INPUT: Final[str] = "requirements.txt"
_DEFAULT_OUTPUT: Final[str] = "upgradable.txt"
_DIM: Final[str] = "\033[2m"
_GREEN: Final[str] = "\033[32m"
_RESET: Final[str] = "\033[0m"
_EDITABLE_RE = re.compile(r"^\s*(?:-e|--editable)\b")


def parse_freeze(path: Path) -> dict[str, str]:
    installed: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if _EDITABLE_RE.match(line):
            continue
        if "@" in line:
            continue
        name, sep, version = line.partition("==")
        if not sep:
            continue
        name = name.strip()
        version = version.strip()
        if not name or not version:
            continue
        installed[name] = version
    return installed


def fetch_latest(session: requests.Session, name: str) -> tuple[str, str | None]:
    try:
        r = session.get(f"https://pypi.org/pypi/{name}/json", timeout=_TIMEOUT)
        if r.status_code == 404:
            return name, None
        r.raise_for_status()
        return name, str(r.json()["info"]["version"])
    except (requests.RequestException, KeyError, ValueError):
        return name, None


def find_upgradable(
    installed: dict[str, str],
    *,
    max_workers: int = _MAX_WORKERS,
) -> dict[str, tuple[str, str]]:
    if not installed:
        return {}
    latest: dict[str, str | None] = {}
    with requests.Session() as session:
        session.headers["User-Agent"] = "requirements-updater/1.0"
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(fetch_latest, session, name): name for name in installed}
            for fut in as_completed(futures):
                name, ver = fut.result()
                latest[name] = ver
    upgradable: dict[str, tuple[str, str]] = {}
    for name, current in installed.items():
        new = latest.get(name)
        if new is None:
            continue
        try:
            is_newer = Version(new) > Version(current)
        except InvalidVersion:
            is_newer = new != current
        if is_newer:
            upgradable[name] = (current, new)
    return upgradable


def render(
    installed: dict[str, str],
    upgradable: dict[str, tuple[str, str]],
) -> str:
    lines: list[str] = []
    for name, current in installed.items():
        if name in upgradable:
            _, new = upgradable[name]
            lines.append(f"{name} {current} {_GREEN}{new}{_RESET}")
        else:
            lines.append(f"{name} {_DIM}{current} {current}{_RESET}")
    return "\n".join(lines)


def write_upgradable(
    path: Path,
    upgradable: dict[str, tuple[str, str]],
) -> None:
    path.write_text(
        "\n".join(f"{name}=={new}" for name, (_, new) in upgradable.items()),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="upgradable",
        description="Show packages with newer versions available on PyPI.",
    )
    parser.add_argument(
        "src",
        nargs="?",
        default=_DEFAULT_INPUT,
        type=Path,
        help=f"pip freeze output (default: {_DEFAULT_INPUT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=Path(_DEFAULT_OUTPUT),
        type=Path,
        help=f"file to write upgradable pins to (default: {_DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=_MAX_WORKERS,
        help=f"concurrent requests (default: {_MAX_WORKERS})",
    )
    args = parser.parse_args(argv)
    if not args.src.is_file():
        print(f"error: file not found: {args.src}", file=sys.stderr)
        return 1
    installed = parse_freeze(args.src)
    upgradable = find_upgradable(installed, max_workers=args.workers)
    write_upgradable(args.output, upgradable)
    report = render(installed, upgradable)
    if report:
        print(report)
    print(f"\n{len(upgradable)} upgradable package(s) written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
