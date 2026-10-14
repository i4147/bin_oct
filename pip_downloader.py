#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a text file containing a list of PyPI package names (one per line, ignoring blank lines and lines beginning with a "#" comment marker), looks up each package's metadata on the public Python Package Index, and downloads a source distribution archive for each package into a local output folder. The script should take the path to the package-list file as its single command-line argument and print a usage message and exit cleanly if the argument is missing or incorrect.
For each package, the script should query the PyPI JSON metadata for the latest release, inspect the list of available distribution files, and prefer source archives in the order of .tar.gz, then .tar.bz2, then .zip. Each downloaded file should be saved into a "downloads" directory created automatically if it does not exist, using the original filename provided by the index. The script should handle HTTP requests with redirects enabled, a reasonable timeout, and a descriptive User-Agent header, and should reuse a single network session for all requests.
Error handling is important: a failure for one package (unknown package name, network error, missing source archive, or a failed download) must not stop processing of the remaining packages. Report each package's outcome clearly to the user in the console, such as success, skipped because no preferred source archive exists, or the specific error encountered, and finish with a brief summary showing how many packages were downloaded successfully and how many failed or were skipped.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from urllib.parse import quote
import httpx

PREFERRED_EXTENSIONS = (".tar.gz", ".tar.bz2", ".zip")


def main():
    if len(sys.argv) != 2:
        msg = f"Usage: python {sys.argv[0]} <package-list-file>"
        raise SystemExit(msg)
    package_file = Path(sys.argv[1])
    output_dir = Path("downloads")
    output_dir.mkdir(exist_ok=True)
    packages = [
        line.strip()
        for line in package_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    with httpx.Client(
        follow_redirects=True,
        timeout=60.0,
        headers={"User-Agent": "pypi-package-downloader/1.0"},
    ) as client:
        for package in packages:
            try:
                api_url = f"https://pypi.org/pypi/{quote(package, safe='')}/json"
                response = client.get(api_url)
                response.raise_for_status()
                data = response.json()
                files = data.get("urls", [])
                selected = None
                for extension in PREFERRED_EXTENSIONS:
                    selected = next(
                        (item for item in files if item.get("filename", "").lower().endswith(extension)),
                        None,
                    )
                    if selected:
                        break
                if selected is None:
                    selected = next(
                        (item for item in files if item.get("filename", "").lower().endswith(".whl")),
                        None,
                    )
                if selected is None:
                    print(f"SKIP {package}: no supported archive or wheel for latest release")
                    continue
                filename = Path(selected["filename"]).name
                destination = output_dir / filename
                with client.stream("GET", selected["url"]) as download:
                    download.raise_for_status()
                    with destination.open("wb") as file:
                        for chunk in download.iter_bytes():
                            file.write(chunk)
                print(f"Downloaded {package} {data['info']['version']}: {destination}")
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                print(f"ERROR {package}: {exc}")


if __name__ == "__main__":
    main()
