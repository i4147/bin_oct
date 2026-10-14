#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that manages a directory of pre-built Python wheel (.whl) packages, identifying and removing outdated or unwanted wheel files so that only the appropriate builds remain. The script should scan a given directory (defaulting to the current working directory) for wheel files and parse each filename to extract the package name, version, and target platform/Python tag. It should recognize a specific set of supported platform tags, including pure-Python "any" builds and several ARM Linux builds for Python 3.7 and 3.12. Filenames that do not match the expected wheel naming convention should be ignored safely.
Key behaviors:
- For packages that carry a date suffix in their version string (for example, a trailing "-YYYYMMDD" stamp), keep only the newest dated build of each package and delete older dated builds.
- Maintain a configurable blocklist of package names that must not be installed as generic pure-Python "any" wheels; any such wheels found should be removed, while other packages remain untouched.
- Only delete files that the script has positively identified as matching the criteria; never remove unrelated files or subdirectories.
- Operate on the files passed in as a list of filenames and resolve them against the target directory, so the cleanup logic can be called programmatically as well as run from the command line.
- Report clearly to the user which wheel files were kept and which were removed, and handle missing directories or permission errors gracefully with informative messages rather than crashing.
- Provide a safe dry-run option so the user can preview deletions before they happen.
The output should be a deterministic cleanup of the wheel directory, with a concise summary of actions taken.
---"""

from __future__ import annotations
import os
from pathlib import Path
import re

WHL_DIRECTORY = Path()
WHL_PATTERN = re.compile(
    r"(?P<name>[\w\-]+)"
    r"-(?P<version>[\d\.]+(?:-\d{8})?)"
    r"-(?P<python>"
    r"py3-none-any"
    r"|cp37-abi3-linux_armv8l"
    r"|cp312-cp312-linux_armv8l"
    r"|cp312-cp312-linux_arm"
    r"|py3-none-linux_armv8l"
    r")\.whl"
)
PY3_NONE_ANY_BLOCKLIST: frozenset[str] = frozenset({"pycryptodome", "matplotlib"})


def _parse_wheel(filename: str) -> tuple[str, str, str] | None:
    match = WHL_PATTERN.match(filename)
    if match is None:
        return None
    return match.group("name"), match.group("version"), match.group("python")


def _latest_dates(parsed: list[tuple[str, str, str, str]]) -> dict[str, str]:
    latest: dict[str, str] = {}
    for _, name, version, _ in parsed:
        if "-" not in version:
            continue
        date_part = version.rsplit("-", 1)[-1]
        if date_part > latest.get(name, ""):
            latest[name] = date_part
    return latest


def cleanup_wheels(whl_files: list[str], directory: Path = WHL_DIRECTORY) -> int:
    parsed: list[tuple[str, str, str, str]] = []
    for filename in whl_files:
        info = _parse_wheel(filename)
        if info is not None:
            parsed.append((filename, *info))
    latest_versions = _latest_dates(parsed)
    deleted = 0
    for filename, name, version, python_variant in parsed:
        blocked_py3 = name in PY3_NONE_ANY_BLOCKLIST and python_variant == "py3-none-any"
        outdated = "-" in version and version.rsplit("-", 1)[-1] != latest_versions.get(name)
        if not (blocked_py3 or outdated):
            continue
        (directory / filename).unlink()
        print(f"Deleted: {filename}")
        deleted += 1
    return deleted


def main() -> None:
    whl_files = [f for f in os.listdir(WHL_DIRECTORY) if f.endswith(".whl")]
    deleted = cleanup_wheels(whl_files)
    print(f"Number of files deleted: {deleted}")


if __name__ == "__main__":
    main()
