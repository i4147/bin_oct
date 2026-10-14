#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line tool for downloading Python package distributions from a Python package index (such as PyPI) that are compatible with the current interpreter and platform. The user supplies one or more package requirement specifications (for example, a package name with an optional version constraint) and optionally a target directory and an alternative index URL. The tool should resolve each requirement against the index's simple repository listing, select the newest release that satisfies the version specifier and is not yanked, and then choose the most suitable distribution file for the running environment, preferring wheels whose compatibility tags match the local Python implementation, version, and operating system, and falling back to source distributions when no compatible wheel exists.
Key behaviors to include:
- Accept requirements in standard dependency-specifier syntax, handle invalid input gracefully, and report clearly which packages or versions could not be found or satisfied.
- Respect each file's declared Python version requirement, skipping releases whose requirement excludes the current interpreter.
- Verify the integrity of each downloaded file against the SHA-256 hash published by the index, and discard or flag any mismatched download.
- Stream downloads to disk in chunks, showing a live progress indicator with transfer speed and estimated remaining time, and avoid re-downloading files that already exist and pass verification.
- Follow redirects and resolve relative file links correctly, with sensible timeouts and clear handling of network or HTTP errors.
- Provide a dry-run or summary mode that lists what would be downloaded without fetching the files.
- Log progress and warnings through a clean logging setup, with a verbosity option.
- Exit with a non-zero status code if any requested package fails to download, and zero otherwise.
- Produce a concise final report listing each downloaded file, its destination path, and its size.
The script should be self-contained, robust to malformed index entries, and designed as a practical command-line utility that a developer could run from a terminal.
---"""

from __future__ import annotations
import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
from urllib.parse import unquote, urljoin, urlparse
import httpx
from loguru import logger
from packaging.requirements import Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.tags import Tag, compatible_tags, cpython_tags, interpreter_name, interpreter_version
from packaging.utils import (
    InvalidSdistFilename,
    InvalidWheelFilename,
    canonicalize_name,
    parse_sdist_filename,
    parse_wheel_filename,
)
from packaging.version import InvalidVersion, Version
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn, TransferSpeedColumn

PYPI = "https://pypi.org/simple/"
ACCEPT = "application/vnd.pypi.simple.v1+json"
CHUNK = 1024 * 1024
NO_TAG = 10**9


@dataclass(frozen=True, slots=True)
class Link:
    url: str
    filename: str
    requires_python: str | None = None
    yanked: bool = False
    sha256: str | None = None


def current_tags() -> list[Tag]:
    py = sys.version_info[:2]
    interp = f"{interpreter_name()}{interpreter_version()}"
    tags = list(cpython_tags(py)) if interpreter_name() == "cp" else []
    tags += list(compatible_tags(py, interp))
    return tags


def fetch_links(client: httpx.Client, name: str) -> list[Link]:
    url = urljoin(PYPI, canonicalize_name(name) + "/")
    r = client.get(url, headers={"Accept": ACCEPT})
    r.raise_for_status()
    base = str(r.url)
    out = []
    for f in r.json().get("files", []):
        full = urljoin(base, f["url"])
        out.append(
            Link(
                url=full,
                filename=unquote(urlparse(full).path.rsplit("/", 1)[-1]),
                requires_python=f.get("requires-python"),
                yanked=bool(f.get("yanked")),
                sha256=(f.get("hashes") or {}).get("sha256"),
            )
        )
    return out


def py_ok(spec: str | None) -> bool:
    if not spec:
        return True
    try:
        return SpecifierSet(spec).contains(f"{sys.version_info.major}.{sys.version_info.minor}", prereleases=True)
    except InvalidSpecifier:
        return True


def select(links: list[Link], req: Requirement) -> tuple[Link, Version] | None:
    tag_index = {t: i for i, t in enumerate(current_tags())}
    best_key: tuple[Version, int] | None = None
    best: tuple[Link, Version] | None = None
    for link in links:
        if link.yanked or not py_ok(link.requires_python):
            continue
        fn = link.filename
        if fn.endswith(".whl"):
            try:
                name, version, _, tags = parse_wheel_filename(fn)
            except (InvalidWheelFilename, InvalidVersion):
                continue
            if canonicalize_name(name) != canonicalize_name(req.name):
                continue
            if not req.specifier.contains(version, prereleases=True):
                continue
            prios = [tag_index[t] for t in tags if t in tag_index]
            if not prios:
                continue
            combined = min(prios)
        elif fn.endswith((".tar.gz", ".zip")):
            try:
                name, version = parse_sdist_filename(fn)
            except (InvalidSdistFilename, InvalidVersion):
                continue
            if canonicalize_name(name) != canonicalize_name(req.name):
                continue
            if not req.specifier.contains(version, prereleases=True):
                continue
            combined = NO_TAG
        else:
            continue
        key = (version, -combined)
        if best_key is None or key > best_key:
            best_key = key
            best = (link, version)
    return best


def download(client: httpx.Client, link: Link, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / link.filename
    if dest.exists():
        logger.info("cached: {}", dest)
        return dest
    tmp = dest.with_name(dest.name + ".part")
    tmp.unlink(missing_ok=True)
    sha = hashlib.sha256()
    try:
        with Progress(
            TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("download", filename=link.filename, total=None)
            with client.stream("GET", link.url) as r:
                r.raise_for_status()
                total = r.headers.get("content-length")
                if total and total.isdigit():
                    progress.update(task, total=int(total))
                with tmp.open("wb") as f:
                    for chunk in r.iter_bytes(CHUNK):
                        f.write(chunk)
                        sha.update(chunk)
                        progress.update(task, advance=len(chunk))
        if link.sha256 and sha.hexdigest() != link.sha256:
            msg = f"sha256 mismatch for {link.filename}"
            raise ValueError(msg)
        tmp.replace(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    logger.success("saved {}", dest)
    return dest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Download a package from PyPI.")
    ap.add_argument("requirement", help="e.g. requests or 'requests==2.31.0'")
    ap.add_argument(
        "-d",
        "--dest",
        type=Path,
        default=Path(),
        help="destination directory (default: .)",
    )
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG" if args.verbose else "INFO",
        format="<level>{level: <8}</level> {message}",
    )
    req = Requirement(args.requirement)
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        links = fetch_links(client, req.name)
        result = select(links, req)
        if result is None:
            logger.error("no matching distribution for {}", args.requirement)
            return 1
        link, version = result
        logger.info("selected {} {}", req.name, version)
        path = download(client, link, args.dest.expanduser().resolve())
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
