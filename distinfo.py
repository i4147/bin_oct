#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current Python environment's installed package metadata and reports any packages that have more than one version installed at the same time, which can cause import conflicts and unpredictable behavior.
The script should:
- Discover every site-packages directory associated with the active Python interpreter, including both the system-wide and the per-user locations, and skip any that do not exist or cannot be read without stopping the overall run.
- Inspect the metadata entries installed in those directories (distribution folders ending in common metadata suffixes) and extract each package's normalized name and version string from the folder name, ignoring entries that don't follow the expected naming pattern.
- Group all discovered versions by package name, treating names case-insensitively, so that the same package appearing in multiple locations is correctly identified.
- Identify packages that have two or more distinct versions present and present them in a clear, alphabetically sorted report listing each conflicting package name along with all of its installed versions and the locations where they were found.
- Print a concise summary at the end: if conflicts exist, state how many packages are affected; if none exist, clearly confirm that every package has a single installed version.
- Handle errors gracefully so that permission problems, missing directories, or malformed entries never crash the script.
- Exit with a non-zero status code when conflicts are detected and zero when the environment is clean, so the tool can be used in automated checks.
- Keep the output human-readable in a terminal, with no external dependencies beyond the Python standard library.
---"""

from __future__ import annotations
from collections import defaultdict
import contextlib
from pathlib import Path
import re
import site


def get_site_packages_dirs():
    dirs = []
    with contextlib.suppress(Exception):
        dirs.extend(site.getsitepackages())
    dirs.append(site.getusersitepackages())
    return list(dict.fromkeys(dirs))


def parse_pkg_info(dirname):
    m = re.match(r"(.+)-(\d+.*?)(\.dist-info|\.egg-info)$", dirname)
    if m:
        return m.group(1).lower(), m.group(2)
    return None, None


def find_multiple_versions() -> None:
    pkg_versions = defaultdict(set)
    for sp_dir in get_site_packages_dirs():
        sp_path = Path(sp_dir)
        if not sp_path.is_dir():
            continue
        for entry in sp_path.iterdir():
            if entry.name.endswith((".dist-info", ".egg-info")):
                name, version = parse_pkg_info(entry.name)
                if name:
                    pkg_versions[name].add(version)
    for pkg, versions in sorted(pkg_versions.items()):
        if len(versions) > 1:
            print(f"\nPackage: {pkg}")
            for v in sorted(versions):
                print(f"  - Version: {v}")
    print("\nDone.")


if __name__ == "__main__":
    find_multiple_versions()
