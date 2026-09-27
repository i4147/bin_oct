#!/data/data/com.termux/files/home/.local/bin/python
"""
List the packages published by a PyPI user (or organisation) and, optionally,
download the latest release of each of them.

The list of package names is always saved to ``<user>.txt`` in the current
working directory, one package per line.

Examples
--------
    python pypi_user_packages.py micropython-lib
    python pypi_user_packages.py https://pypi.org/user/micropython-lib/
    python pypi_user_packages.py micropython-lib -d
    python pypi_user_packages.py micropython-lib -d -b requests -o ./pkgs
    python pypi_user_packages.py micropython-lib -d -b pycurl -m 5
    python pypi_user_packages.py micropython-lib -d -b aria2c -m 5
    python pypi_user_packages.py micropython-lib -d -m 5          # httpx, 8 jobs

Backends
--------
* ``httpx`` (default) - uses the third-party ``httpx`` library. Downloads run
                        through an async parallel downloader with 8 concurrent
                        transfers (matching an 8-core machine).
* ``urllib``          - pure Python, stdlib only.
* ``requests``        - uses the third-party ``requests`` library.
* ``pycurl``          - uses ``pycurl`` (libcurl bindings).
* ``aria2c``          - shells out to the ``aria2c`` command-line downloader.

Notes
-----
* The profile URL is followed through redirects, so both
  https://pypi.org/user/<name>/ and https://pypi.org/org/<name>/ work.
* File sizes are read from the JSON API (https://pypi.org/pypi/<pkg>/json) and
  any file larger than the limit (10 MiB by default) is skipped. A streaming
  guard in each backend aborts a download that turns out to be too large.
* Parallelism is only applied for the ``httpx`` backend. All other backends
  run sequentially.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PYPI_BASE = "https://pypi.org"
USER_AGENT = "pypi-user-packages/1.3"
DEFAULT_MAX_MIB = 10.0
CHUNK_SIZE = 64 * 1024
ARIA2C_BIN = "aria2c"
DEFAULT_BACKEND = "httpx"
DEFAULT_JOBS = 8

_PROJECT_RE = re.compile(r"^/project/([^/?#]+)/?$")
_PAGE_RE = re.compile(r"[?&]page=(\d+)")


class _ProfileParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._snippet_hrefs: list[str] = []
        self._all_project_hrefs: list[str] = []
        self.page_numbers: set[int] = set()

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs = dict(attrs)
        href = attrs.get("href") or ""

        m = _PAGE_RE.search(href)
        if m:
            self.page_numbers.add(int(m.group(1)))

        if _PROJECT_RE.match(href):
            self._all_project_hrefs.append(href)
            classes = (attrs.get("class") or "").split()
            if "package-snippet" in classes:
                self._snippet_hrefs.append(href)

    def project_names(self) -> list[str]:
        hrefs = self._snippet_hrefs or self._all_project_hrefs
        names: list[str] = []
        seen: set[str] = set()
        for href in hrefs:
            match = _PROJECT_RE.match(href)
            if not match:
                continue
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                names.append(name)
        return names


def _page_of(url: str) -> int:
    m = re.search(r"[?&]page=(\d+)", url)
    return int(m.group(1)) if m else 1


def _with_page(url: str, page: int) -> str:
    return f"{url.split('?', 1)[0]}?page={page}"


def check_backend(backend: str) -> None:
    if backend == "requests":
        try:
            import requests  # noqa: F401
        except ImportError:
            sys.exit(
                "backend 'requests' selected but 'requests' is not installed "
                "(pip install requests)"
            )
    elif backend == "pycurl":
        try:
            import pycurl  # noqa: F401
        except ImportError:
            sys.exit(
                "backend 'pycurl' selected but 'pycurl' is not installed "
                "(pip install pycurl)"
            )
    elif backend == "aria2c":
        if shutil.which(ARIA2C_BIN) is None:
            sys.exit(
                f"backend 'aria2c' selected but '{ARIA2C_BIN}' was not found "
                "on PATH (install aria2, e.g. 'apt install aria2' or "
                "'brew install aria2')"
            )
    elif backend == "httpx":
        try:
            import httpx  # noqa: F401
        except ImportError:
            sys.exit(
                "backend 'httpx' selected but 'httpx' is not installed "
                "(pip install httpx)"
            )


def fetch_bytes(url: str, backend: str = DEFAULT_BACKEND, timeout: float = 30.0):
    if backend == "aria2c":
        backend = "urllib"

    if backend == "pycurl":
        return _fetch_pycurl(url, timeout)
    if backend == "requests":
        return _fetch_requests(url, timeout)
    if backend == "httpx":
        return _fetch_httpx(url, timeout)
    return _fetch_urllib(url, timeout)


def _fetch_urllib(url: str, timeout: float):
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.geturl()


def _fetch_requests(url: str, timeout: float):
    import requests

    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    return resp.content, resp.url


def _fetch_httpx(url: str, timeout: float):
    import httpx

    resp = httpx.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
        follow_redirects=True,
    )
    resp.raise_for_status()
    return resp.content, str(resp.url)


def _fetch_pycurl(url: str, timeout: float):
    import pycurl

    buf = io.BytesIO()
    curl = pycurl.Curl()
    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.FOLLOWLOCATION, True)
        curl.setopt(pycurl.MAXREDIRS, 10)
        curl.setopt(pycurl.TIMEOUT, int(timeout))
        curl.setopt(pycurl.USERAGENT, USER_AGENT)
        curl.setopt(pycurl.WRITEFUNCTION, buf.write)
        curl.perform()
        status = curl.getinfo(pycurl.RESPONSE_CODE)
        effective = curl.getinfo(pycurl.EFFECTIVE_URL)
    finally:
        curl.close()
    if status >= 400:
        raise HTTPError(url, status, f"HTTP {status}", None, None)
    return buf.getvalue(), effective


class FileTooLarge(Exception):
    pass


def download_file(
    url: str,
    dest: Path,
    backend: str,
    max_bytes: int,
    timeout: float = 60.0,
) -> int:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.parent / (dest.name + ".part")

    try:
        if backend == "pycurl":
            written = _download_pycurl(url, tmp, max_bytes, timeout)
        elif backend == "requests":
            written = _download_requests(url, tmp, max_bytes, timeout)
        elif backend == "aria2c":
            written = _download_aria2c(url, tmp, max_bytes, timeout)
        else:
            written = _download_urllib(url, tmp, max_bytes, timeout)
        tmp.replace(dest)
        return written
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _download_urllib(url: str, tmp: Path, max_bytes: int, timeout: float) -> int:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        declared = resp.headers.get("Content-Length")
        if declared and int(declared) > max_bytes:
            raise FileTooLarge(f"Content-Length {declared} > {max_bytes}")
        written = 0
        with open(tmp, "wb") as fh:
            while True:
                chunk = resp.read(CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise FileTooLarge(f"exceeded {max_bytes} bytes")
                fh.write(chunk)
    return written


def _download_requests(url: str, tmp: Path, max_bytes: int, timeout: float) -> int:
    import requests

    written = 0
    with requests.get(
        url, headers={"User-Agent": USER_AGENT}, timeout=timeout, stream=True
    ) as resp:
        resp.raise_for_status()
        declared = resp.headers.get("Content-Length")
        if declared and int(declared) > max_bytes:
            raise FileTooLarge(f"Content-Length {declared} > {max_bytes}")
        with open(tmp, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                written += len(chunk)
                if written > max_bytes:
                    raise FileTooLarge(f"exceeded {max_bytes} bytes")
                fh.write(chunk)
    return written


def _download_pycurl(url: str, tmp: Path, max_bytes: int, timeout: float) -> int:
    import pycurl

    written = 0
    aborted = False
    fh = open(tmp, "wb")
    curl = pycurl.Curl()

    def _write(data: bytes) -> int:
        nonlocal written, aborted
        written += len(data)
        if written > max_bytes:
            aborted = True
            return 0
        return fh.write(data)

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.FOLLOWLOCATION, True)
        curl.setopt(pycurl.MAXREDIRS, 10)
        curl.setopt(pycurl.TIMEOUT, int(timeout))
        curl.setopt(pycurl.USERAGENT, USER_AGENT)
        curl.setopt(pycurl.WRITEFUNCTION, _write)
        curl.perform()
        status = curl.getinfo(pycurl.RESPONSE_CODE)
    except pycurl.error as exc:
        if aborted:
            raise FileTooLarge(f"exceeded {max_bytes} bytes") from exc
        raise
    finally:
        curl.close()
        fh.close()

    if status >= 400:
        raise HTTPError(url, status, f"HTTP {status}", None, None)
    return written


def _download_aria2c(url: str, tmp: Path, max_bytes: int, timeout: float) -> int:
    cmd = [
        ARIA2C_BIN,
        "--no-conf=true",
        "--quiet=true",
        "--console-log-level=error",
        "--file-allocation=none",
        "--continue=false",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--check-certificate=true",
        f"--user-agent={USER_AGENT}",
        f"--timeout={int(timeout)}",
        "--max-tries=3",
        f"--max-filesize={max_bytes}",
        f"--out={tmp.name}",
        f"--dir={tmp.parent}",
        url,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout + 60,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("aria2c timed out") from exc

    stderr_text = result.stderr.decode("utf-8", "replace").strip()

    if result.returncode != 0 or not tmp.exists():
        low = stderr_text.lower()
        if "max-filesize" in low or "too large" in low or "exceeds" in low:
            raise FileTooLarge(stderr_text or f"exceeded {max_bytes} bytes")
        raise RuntimeError(
            f"aria2c failed (exit {result.returncode}): {stderr_text or '<no stderr>'}"
        )

    size = tmp.stat().st_size
    if size > max_bytes:
        tmp.unlink(missing_ok=True)
        raise FileTooLarge(f"downloaded {size} bytes > {max_bytes}")

    tmp.with_name(tmp.name + ".aria2").unlink(missing_ok=True)
    return size


async def _download_one_async(
    client,
    url: str,
    dest: Path,
    max_bytes: int,
    sem: asyncio.Semaphore,
) -> tuple[Path, int | None, Exception | None]:
    async with sem:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.parent / (dest.name + ".part")
        written = 0

        try:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()

                declared = resp.headers.get("Content-Length")
                if declared and int(declared) > max_bytes:
                    raise FileTooLarge(f"Content-Length {declared} > {max_bytes}")

                with open(tmp, "wb") as fh:
                    async for chunk in resp.aiter_bytes(CHUNK_SIZE):
                        if not chunk:
                            continue
                        written += len(chunk)
                        if written > max_bytes:
                            raise FileTooLarge(f"exceeded {max_bytes} bytes")
                        fh.write(chunk)

            tmp.replace(dest)
            return dest, written, None
        except BaseException as exc:  # noqa: BLE001
            tmp.unlink(missing_ok=True)
            return dest, None, exc


async def _download_all_async(
    tasks: list[tuple[str, Path]],
    max_bytes: int,
    timeout: float,
    jobs: int,
    on_event,
) -> None:
    import httpx

    sem = asyncio.Semaphore(jobs)

    limits = httpx.Limits(
        max_connections=None,
        max_keepalive_connections=None,
    )

    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
        follow_redirects=True,
        limits=limits,
    ) as client:
        coros = [
            _download_one_async(client, url, dest, max_bytes, sem)
            for url, dest in tasks
        ]
        for coro in asyncio.as_completed(coros):
            dest, written, exc = await coro
            on_event("done", dest, written, exc)


def download_all(
    tasks: list[tuple[str, Path]],
    backend: str,
    max_bytes: int,
    timeout: float,
    on_event,
) -> None:
    if backend == "httpx" and tasks:
        asyncio.run(
            _download_all_async(tasks, max_bytes, timeout, DEFAULT_JOBS, on_event)
        )
        return

    for url, dest in tasks:
        try:
            written = download_file(url, dest, backend, max_bytes, timeout=timeout)
        except BaseException as exc:  # noqa: BLE001
            on_event("done", dest, None, exc)
        else:
            on_event("done", dest, written, None)


def resolve_profile_url(target: str) -> str:
    target = target.strip()
    if "://" in target:
        return target
    return f"{PYPI_BASE}/user/{target.strip('/')}/"


def extract_username(target: str) -> str:
    target = target.strip().rstrip("/")
    if "://" in target:
        target = target.rsplit("/", 1)[-1]

    safe = re.sub(r"[^A-Za-z0-9._-]", "_", target)
    return safe or "pypi_user"


def save_package_list(names: list[str], username: str) -> Path:
    out_path = Path.cwd() / f"{username}.txt"
    out_path.write_text("\n".join(names) + "\n", encoding="utf-8")
    return out_path


def collect_packages(start_url: str, backend: str, timeout: float, quiet: bool = False):
    names: list[str] = []
    seen: set[str] = set()
    visited_pages: set[int] = set()
    page_url: str | None = start_url
    final_url = start_url

    while page_url:
        body, final_url = fetch_bytes(page_url, backend, timeout)
        parser = _ProfileParser()
        parser.feed(body.decode("utf-8", "replace"))

        new = [n for n in parser.project_names() if n not in seen]
        seen.update(new)
        names.extend(new)

        current = _page_of(page_url)
        visited_pages.add(current)
        highest = max(parser.page_numbers) if parser.page_numbers else current

        if new and highest > current and (current + 1) not in visited_pages:
            page_url = _with_page(final_url, current + 1)
            if not quiet:
                print(f"  ... fetching page {current + 1}", file=sys.stderr)
        else:
            page_url = None

    return names, final_url


def fetch_package_files(name: str, backend: str, timeout: float):
    body, _ = fetch_bytes(f"{PYPI_BASE}/pypi/{name}/json", backend, timeout)
    meta = json.loads(body)
    return meta["info"]["version"], meta.get("urls", [])


def _mib(n: int) -> str:
    return f"{n / (1024 * 1024):.2f} MiB"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pypi_user_packages.py",
        description=(
            "List the packages published by a PyPI user/org "
            "and optionally download them. The package list is always "
            "saved to <user>.txt in the current directory."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "user",
        help="PyPI user/org name (e.g. micropython-lib) or a full profile URL",
    )
    p.add_argument(
        "-d",
        "--download",
        action="store_true",
        help="download the packages (latest release of each)",
    )
    p.add_argument(
        "-b",
        "--backend",
        choices=("httpx", "urllib", "requests", "pycurl", "aria2c"),
        default=DEFAULT_BACKEND,
        help=f"HTTP backend to use (default: {DEFAULT_BACKEND}). 'httpx' runs "
        f"parallel async downloads with {DEFAULT_JOBS} concurrent jobs; "
        "'aria2c' shells out to the aria2c binary.",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("pypi-packages"),
        help="directory for downloads (default: ./pypi-packages)",
    )
    p.add_argument(
        "-m",
        "--max-size",
        type=float,
        default=DEFAULT_MAX_MIB,
        metavar="MIB",
        help=f"skip files larger than this, in MiB (default: {DEFAULT_MAX_MIB:g})",
    )
    p.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=30.0,
        help="per-request timeout in seconds (default: 30)",
    )
    p.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress progress messages on stderr",
    )
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    check_backend(args.backend)

    max_bytes = int(args.max_size * 1024 * 1024)
    profile_url = resolve_profile_url(args.user)
    username = extract_username(args.user)

    if not args.quiet:
        print(f"Fetching {profile_url} ...", file=sys.stderr)

    try:
        names, final_url = collect_packages(
            profile_url, args.backend, args.timeout, args.quiet
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not fetch the profile page: {exc}", file=sys.stderr)
        return 1

    if final_url.rstrip("/") != profile_url.rstrip("/") and not args.quiet:
        print(f"  resolved to {final_url}", file=sys.stderr)

    if not names:
        print("No packages found on that profile page.", file=sys.stderr)
        return 1

    list_path = save_package_list(names, username)
    print(f"{len(names)} package(s) -> {list_path}")
    for name in names:
        print(f"  {name}")

    if not args.download:
        return 0

    outdir: Path = args.output
    outdir.mkdir(parents=True, exist_ok=True)
    parallel = args.backend == "httpx"
    print(
        f"\nDownloading into {outdir.resolve()} "
        f"(backend={args.backend}, limit={args.max_size:g} MiB"
        + (f", jobs={DEFAULT_JOBS}" if parallel else "")
        + ")"
    )

    tasks: list[tuple[str, Path]] = []
    have_count = 0

    for index, name in enumerate(names, 1):
        prefix = f"[{index}/{len(names)}] {name}"
        try:
            version, files = fetch_package_files(name, args.backend, args.timeout)
        except Exception as exc:  # noqa: BLE001
            print(f"{prefix}: metadata error: {exc}", file=sys.stderr)
            continue

        if not files:
            print(f"{prefix}: no downloadable files for {version}")
            continue

        print(f"{prefix} {version}")
        for entry in files:
            filename = entry["filename"]
            size = int(entry.get("size") or 0)
            url = entry["url"]

            if size and size > max_bytes:
                print(f"    skip {filename} ({_mib(size)} > limit)")
                continue

            dest = outdir / name / filename
            if dest.exists():
                print(f"    have {filename}")
                have_count += 1
                continue

            tasks.append((url, dest))

    total_files = 0
    failures = 0

    def on_event(kind: str, dest: Path, written, exc) -> None:
        nonlocal total_files, failures
        if exc is None:
            total_files += 1
            print(f"    got  {dest.name} ({_mib(written)})")
        elif isinstance(exc, FileTooLarge):
            print(f"    skip {dest.name} ({exc})")
        else:
            failures += 1
            print(f"    fail {dest.name}: {exc}", file=sys.stderr)

    download_all(
        tasks,
        args.backend,
        max_bytes,
        timeout=max(args.timeout, 60.0),
        on_event=on_event,
    )

    print(
        f"\nDone. {total_files} file(s) downloaded"
        f"{f', {have_count} already present' if have_count else ''}"
        f"{f', {failures} failed' if failures else ''}"
        f" -> {outdir.resolve()}"
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
