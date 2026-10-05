#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans all Python site-packages directories (system, global, and user) to detect packages installed with multiple different versions simultaneously.
It should locate directories ending in ".dist-info" or ".egg-info", parse each name into a package name and version using a regular expression, and group versions by lowercased package name.
Finally, it should print out only the packages that have more than one distinct version installed, listing each version under the package name, and print "Done." when finished."""

from __future__ import annotations
import contextlib
import re
import site
from collections import defaultdict
from pathlib import Path


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
