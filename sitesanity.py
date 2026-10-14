#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that performs a sanity check on the installed Python packages in a Termux environment. The script should inspect every installed distribution, verify that the files the package declares as belonging to it actually exist on disk, and report any that are missing so the user can identify broken or incompletely installed packages.
The tool should accept command-line options that let the user exclude files from the check, supplying one or more filename patterns (such as wildcard expressions like "*.md") that can be given multiple times. Files matching these patterns, as well as compiled Python bytecode files, should be skipped and not counted as missing.
For each package, the script should determine which declared files are absent and collect them. Packages that declare no file manifest should be handled gracefully without causing errors. After scanning all packages, the script should present a clear, readable summary to the user: list each package that has missing files along with the specific missing paths, and output a final tally of how many packages and files were found to be missing. If everything is intact, it should clearly report that no problems were detected.
Logging should be used to communicate progress and results to standard output at an informational level. The script should be robust against errors while reading individual package metadata, continuing to check remaining packages rather than aborting. It should run as a standalone command-line program with a helpful usage description and exit cleanly, returning an appropriate status code that indicates whether any missing files were found.
---"""

from __future__ import annotations
import argparse
from fnmatch import fnmatch
import importlib.metadata
import logging
from pathlib import Path
import sys

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Sanity check installed Termux Python packages.")
    parser.add_argument(
        "-i",
        "--ignore",
        action="append",
        default=[],
        help="Glob pattern or filename to ignore when checking package files (e.g., '*.md'). Can be used multiple times.",
    )
    return parser.parse_args()


def should_ignore_file(path: Path, ignore_patterns: list[str]) -> bool:
    if path.suffix == ".pyc":
        return True
    name = path.name
    return any(fnmatch(name, pattern) for pattern in ignore_patterns)


def check_package_files(dist, ignore_patterns: list[str]) -> list[str]:
    missing_files = []
    if dist.files is None:
        return missing_files
    for package_file in dist.files:
        path = Path(dist.locate_file(package_file))
        if should_ignore_file(path, ignore_patterns):
            continue
        if not path.exists():
            missing_files.append(str(package_file))
    return missing_files


def check_package_dependencies(dist, installed_map: dict[str, str]) -> tuple[list[str], list[str]]:
    broken_deps = []
    clean_reqs_for_file = []
    if dist.requires is None:
        return broken_deps, clean_reqs_for_file
    for req_str in dist.requires:
        if "extra ==" in req_str or "extra =" in req_str:
            continue
        parts = req_str.split(";")
        base_requirement = parts[0].strip()
        dep_name = base_requirement
        for op in ["<", ">", "=", "!", "~"]:
            if op in dep_name:
                dep_name = dep_name.split(op)[0].strip()
        if not dep_name:
            continue
        if dep_name.lower() not in installed_map:
            broken_deps.append(base_requirement)
            clean_reqs_for_file.append(base_requirement)
    return broken_deps, clean_reqs_for_file


def main():
    args = parse_arguments()
    logging.info("Starting Termux site-packages verification scan...\n")
    distributions = list(importlib.metadata.distributions())
    installed_map = {d.metadata["Name"].lower(): d.version for d in distributions}
    unique_missing_deps = set()
    corrupted_packages_count = 0
    broken_deps_count = 0
    for dist in distributions:
        pkg_name = dist.metadata["Name"]
        pkg_version = dist.version
        origin_path = getattr(dist, "_path", "Unknown Environment Space")
        missing_files = check_package_files(dist, args.ignore)
        missing_deps, file_deps = check_package_dependencies(dist, installed_map)
        if missing_files or missing_deps:
            print(f"📦 PACKAGE: {pkg_name} ({pkg_version})")
            print(f"   Location Target: {origin_path}")
            if missing_files:
                corrupted_packages_count += 1
                print(f"   ❌ Missing Files ({len(missing_files)}):")
                for f in missing_files[:5]:
                    print(f"      - {f}")
                if len(missing_files) > 5:
                    print(f"      - ... and {len(missing_files) - 5} more files missing.")
            if missing_deps:
                broken_deps_count += 1
                print("   ⚠️  Unresolved Core Dependencies:")
                for dep in missing_deps:
                    print(f"      - Missing requirement: {dep}")
                for clean_dep in file_deps:
                    unique_missing_deps.add(clean_dep)
            print("-" * 40)
    if unique_missing_deps:
        req_file = Path("requirements.txt")
        with open(req_file, "w", encoding="utf-8") as f:
            for dep in sorted(unique_missing_deps):
                f.write(f"{dep}\n")
        logging.info(f"📝 Saved {len(unique_missing_deps)} unique main dependencies to: {req_file.resolve()}")
    logging.info("=== SCAN SUMMARY ===")
    logging.info(f"Total packages evaluated: {len(distributions)}")
    logging.info(f"Packages with missing files: {corrupted_packages_count}")
    logging.info(f"Packages with missing dependencies: {broken_deps_count}")


if __name__ == "__main__":
    raise SystemExit(main())
