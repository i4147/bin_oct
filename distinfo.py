#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script that scans every Python site-packages directory visible to the current interpreter and reports any installed package that has more than one version present on disk.

Requirements:

**Purpose:** Detect duplicate installations of the same distribution (for example, two different versions of a package left behind by separate installs) by inspecting installed metadata directories, without importing any of the packages.

**Shebang and header:** Start with a Termux-style shebang pointing to `/data/data/com.termux/files/usr/bin/env python`. Enable postponed annotations via `from __future__ import annotations`.

**Dependencies:** Use only the Python standard library: `contextlib`, `re`, `site`, `collections.defaultdict`, and `pathlib.Path`. No third-party packages.

**Components to implement:**

1. A function that collects the set of site-packages directories to scan. It should:
   - Attempt to get the global site-packages directories from `site` inside a suppressing context manager so that any exception is silently ignored (the function may not exist on some builds).
   - Always append the user site-packages directory.
   - Remove duplicates while preserving the original order (use `dict.fromkeys`).
   - Return a list.

2. A function that parses a metadata directory name. It takes a single directory name string and matches it against the pattern: a package name (one or more characters, greedy-minimal), a hyphen, a version beginning with a digit and extending lazily, followed by either `.dist-info` or `.egg-info` at the end of the string. On a match, return the package name lowercased and the version string. On no match, return a tuple of two `None` values. Note that the dot in the version pattern is unescaped and matches any character, and the name group is greedy, so the split occurs at the last hyphen followed by a digit that still satisfies the suffix rule; preserve this behavior exactly.

3. A main function, `find_multiple_versions`, returning nothing, that:
   - Creates a `defaultdict` mapping package name to a set of version strings.
   - Iterates over each site-packages directory from step 1. Wrap the path in `Path`, skip it if it is not an existing directory, then iterate its entries.
   - For each entry whose name ends with `.dist-info` or `.egg-info`, parse the name; if a package name was returned (not `None`), add the version to that package's set.
   - After scanning, iterate packages in sorted alphabetical order. For each package with more than one distinct version, print a blank line, then `Package: <name>`, then for each version in sorted order print an indented line `  - Version: <version>`.
   - Finally print a blank line followed by `Done.` regardless of whether duplicates were found.

4. Entry point: when the file is run directly (not imported), call `find_multiple_versions()`.

**Inputs and outputs:** No command-line arguments and no stdin. The only output is printed text to standard output in the format described above. The script does not write files and does not modify the environment.

**Error handling and edge cases:**
- Failure to retrieve global site-packages directories must not crash the script.
- Non-existent or non-directory site-packages paths must be skipped silently.
- Metadata entries that do not match the naming pattern must be ignored without error.
- Duplicate site-packages directories returned by `site` must be scanned only once.
- Package names are compared in lowercase, so case variants merge into one entry, but version strings are kept as extracted.
- Packages with only a single version produce no output.
- If no duplicates exist, output is just the trailing `Done.` line preceded by a blank line.

**Style:** Keep the code short, idiomatic, and readable, with type hints only where stated (the main function returns `None`). Use f-strings for printing. Do not add comments beyond what is needed for clarity.

Output the complete script as your final deliverable.
---"""

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
