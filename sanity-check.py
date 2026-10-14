#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a Debian/Ubuntu package health and update checker for a Linux system. The script should run as a command-line tool and perform the following:
- Enumerate all packages currently installed on the system, along with each package's installation status and version, and present them in a readable listing.
- Accept one or more package names from the user (via command-line arguments or an interactive prompt) and verify whether each named package is correctly installed and in a healthy state, reporting a clear OK or a descriptive problem status for each. Handle packages that are not found or cannot be queried gracefully.
- Check whether system updates are available by simulating an upgrade without actually installing anything, and summarize which packages would be upgraded, with a clear message when the system is up to date.
- Handle errors robustly at every stage: if the system package tools are unavailable or a command fails, print a clear error message and exit with a non-zero status code rather than crashing with a raw traceback.
- Provide a main entry point that lets the user choose which operation to run (list installed packages, check package health, or check for updates), or run all of them in sequence when requested.
- Print results in a clean, human-readable format suitable for terminal use, with consistent labeling and clear section headers.
- Never modify the system: all operations must be read-only and must not install, remove, or upgrade any packages.
---"""

from __future__ import annotations
import sys
from dh import runcmd


def get_installed_packages() -> list[str]:
    try:
        _ret, txt, _err = runcmd(
            ["dpkg-query", "-W", "-f='${Package}\t${Status}\t${Version}\n'"],
            show_output=True,
        )
        return txt.splitlines()
    except:
        print("Error listing installed packages")
        sys.exit(1)


def check_package_health(package_name: str):
    try:
        _ret, txt, _err = runcmd(["dpkg", "-l", package_name], show_output=True)
        lines = txt.splitlines()
        for line in lines:
            if package_name in line:
                status = line.split()[0]
                if status.startswith("ii"):
                    return (True, "OK")
                return (False, f"Status: {status}")
    except:
        return (False, "Error checking package")


def check_for_updates() -> str:
    try:
        _res, txt, _err = runcmd(["apt-get", "-s", "upgrade"], show_output=True)
        return txt
    except:
        return "Error checking for updates"


def main() -> None:
    print("=== Installed Packages Sanity Check ===")
    installed_pkgs = get_installed_packages()
    print(f"Found {len(installed_pkgs)} installed packages.\n")
    issues_found = 0
    for pkg_info in installed_pkgs:
        pkg_name, _status, _version = pkg_info.split("\t")
        pkg_name = pkg_name.strip("'")
        is_ok, msg = check_package_health(pkg_name)
        if not is_ok:
            print(f"[!] {pkg_name}: {msg}")
            issues_found += 1
    print("\n=== Update Check ===")
    update_info = check_for_updates()
    if "0 upgraded, 0 newly installed" in update_info:
        print("All packages are up to date.")
    else:
        print("Updates are available. Run 'sudo apt-get upgrade' to update.")
        print("--- Update Info ---")
        print(update_info)
    print("\n=== Summary ===")
    print(f"Issues found: {issues_found}")
    if issues_found == 0:
        print("All packages are properly installed.")
    else:
        print("Some packages may need attention.")


if __name__ == "__main__":
    raise SystemExit(main())
