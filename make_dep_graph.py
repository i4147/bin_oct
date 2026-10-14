#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that inspects the Python environment it runs in and produces a report of all installed third-party packages along with the dependencies each package declares. The tool should locate the active site-packages directory from the interpreter's module search paths, scan each installed distribution's metadata for its declared requirements, and clean up those requirement strings so that only the dependency name (and optionally its version constraint) remains, dropping environment markers and extras noise. The script should gracefully handle cases where the site-packages directory cannot be found, where metadata files are missing or unreadable, or where encoding issues occur, reporting such problems clearly rather than crashing. The final output should be a structured, human-readable summary mapping each installed package to its list of dependencies, with packages that declare no dependencies clearly indicated, and it should optionally be exportable in a machine-readable format such as JSON for further processing. Keep the tool self-contained, runnable from the command line, and focused on read-only inspection of the environment without modifying any installed packages.
---"""

from __future__ import annotations
import json
import os
from pathlib import Path
import re
import sys


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
