#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans the current Python environment's site-packages directory to discover all installed packages and extract their declared dependencies from each package's dist-info METADATA file.
For each package found, parse the "Requires-Dist" lines, strip version specifiers, environment markers, and extras to obtain clean dependency names, then build a dictionary mapping each package name to its list of dependencies.
If no site-packages directory can be located, return an error message string instead.
When run as a script, compute this mapping and output it as formatted JSON (or print the error message if applicable)."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def get_installed_packages_dependencies():
    dependencies = {}
    site_packages_path = None
    for path in sys.path:
        if "site-packages" in path:
            site_packages_path = path
            break
    if not site_packages_path:
        return "Could not find site-packages directory."
    for package_dir in os.listdir(site_packages_path):
        if package_dir.endswith(".dist-info"):
            dist_info_path = os.path.join(site_packages_path, package_dir)
            metadata_path = os.path.join(dist_info_path, "METADATA")
            if Path(metadata_path).exists():
                package_name = package_dir.split(".dist-info")[0]
                package_dependencies = []
                with Path(metadata_path).open(encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("Requires-Dist:"):
                            dep = re.sub(r";.*", "", line.split("Requires-Dist:")[1].strip())
                            dep = re.sub(r"[<>=~]", "", dep).split("(")[0].strip()
                            package_dependencies.append(dep)
                dependencies[package_name] = package_dependencies
    return dependencies


if __name__ == "__main__":
    all_dependencies = get_installed_packages_dependencies()
    if isinstance(all_dependencies, str):
        print(all_dependencies)
    else:
        output_file = "package_dependencies.json"
        with Path(output_file).open("w", encoding="utf-8") as f:
            json.dump(all_dependencies, f, indent=4, ensure_ascii=False)
        print(f"Package dependencies saved to {output_file}")
