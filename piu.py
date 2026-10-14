#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line utility for uninstalling pip packages in bulk. The tool should accept one or more package names as command-line arguments and uninstall them from the current Python environment without requiring interactive confirmation. It should also support an optional wildcard mode, triggered by a leading flag, in which each supplied term is treated as a substring pattern that matches any installed package whose name contains that text (case-insensitive). In wildcard mode, all matching installed packages should be collected and uninstalled together, with duplicates removed. In normal mode, package names should be matched case-insensitively against the installed packages so that the user can supply names in any casing, and the canonical installed name should be used when uninstalling.
Inputs: command-line arguments consisting of an optional wildcard flag followed by one or more package names or substring patterns.
Outputs and behavior: if no arguments are given, or if wildcard mode is requested without any patterns, the script should print a brief usage message showing the expected syntax and exit with a non-zero status. The script should enumerate the packages installed in the active environment, report any requested packages that are not installed, and perform the uninstall for the resolved set. It should return or exit with the status code produced by the underlying uninstall operation so that success or failure is reflected to the caller. Provide clear, concise console messages describing what was matched, what was skipped, and what is being removed. Handle the case where nothing matches gracefully by informing the user and exiting without attempting an uninstall.
---"""

from __future__ import annotations
from importlib.metadata import distributions
import sys
from pip._internal.cli.main import main as pip_main


def get_installed_packages() -> list[str]:
    return [dist.metadata["Name"] for dist in distributions() if dist.metadata["Name"] is not None]


def uninstall(packages: list[str]) -> int:
    args = ["uninstall", "-y", *packages]
    return pip_main(args)


def main() -> None:
    argv: list[str] = sys.argv[1:]
    if not argv:
        print("Usage: python piu.py [-w] <package> [<package> ...]")
        sys.exit(1)
    wildcard: bool = argv[0] == "-w"
    patterns: list[str] = argv[1:] if wildcard else argv
    if not patterns:
        print("Usage: python piu.py [-w] <package> [<package> ...]")
        sys.exit(1)
    installed: list[str] = get_installed_packages()
    installed_map: dict[str, str] = {name.lower(): name for name in installed}
    matched: set[str] = set()
    if wildcard:
        for pattern in patterns:
            p: str = pattern.lower()
            for name in installed:
                if p in name.lower():
                    matched.add(name)
    else:
        for pattern in patterns:
            p = pattern.lower()
            if p in installed_map:
                matched.add(installed_map[p])
    if not matched:
        print("No matching packages found")
        return
    uninstall(sorted(matched))


if __name__ == "__main__":
    main()
