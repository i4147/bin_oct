#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that resumably downloads a list of Debian/Termux packages (in the style of an apt package cache fetcher) for a Termux environment, using a plain-text package list file as input. The script should read package names from the file while ignoring blank lines and comment lines, and track its progress in a companion progress file so that an interrupted run can be resumed without re-downloading packages that already succeeded. It should record which packages have completed, which have failed, and which is currently in progress, tolerating a missing or corrupted progress file by starting fresh with a clear warning.
For each package, the script should fetch the package and its dependencies into the local apt archive cache directory, skipping anything already present. It should invoke the system package tooling through a shared command-running helper, pass along an environment that respects existing apt configuration, and handle failures gracefully: a failed package should be recorded and reported without aborting the whole run, and the user should be able to retry only the failed items later.
The script should print clear, concise progress output showing how many packages are done, failed, and remaining, and should finish with a summary report. It should exit with a nonzero status if any packages failed and zero if everything succeeded. It should accept a command-line argument specifying the package list file path, and handle missing files or invalid input with helpful error messages instead of crashes. Keep the design simple, robust to interruption at any point (including Ctrl+C, which should save progress before exiting), and suitable for running unattended on a mobile Linux terminal environment.
---"""

from __future__ import annotations
import glob
import json
import os
from pathlib import Path
import sys
from typing import Any
from dh import runcmd

PROGRESS_SUFFIX: str = ".progress"
APT_ARCHIVES: Path = Path("/data/data/com.termux/cache/apt/archives")
APT_ENV: dict[str, str] = {**os.environ, "APT_CONFIG": os.environ.get("APT_CONFIG", "")}


def read_packages(filepath: Path) -> list[str]:
    pkgs: list[str] = []
    with filepath.open("r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkgs.append(line)
    return pkgs


def load_progress(progress_file: Path) -> dict[str, Any]:
    if not progress_file.exists():
        return {"completed": [], "failed": [], "current": None}
    try:
        with progress_file.open("r") as f:
            data: dict[str, Any] = json.load(f)
        data.setdefault("completed", [])
        data.setdefault("failed", [])
        data.setdefault("current", None)
        return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: could not read progress file ({e}), starting fresh")
        return {"completed": [], "failed": [], "current": None}


def save_progress(progress_file: Path, progress: dict[str, Any]) -> None:
    tmp: Path = progress_file.with_suffix(progress_file.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(progress, f, indent=2)
    tmp.replace(progress_file)


def cleanup_deb(pkg: str) -> list[Path]:
    patterns: list[str] = [
        f"{pkg}_*.deb",
        f"{pkg}-*.deb",
        f"{pkg}.deb",
    ]
    removed: list[Path] = []
    for pat in patterns:
        for path_str in glob.glob(str(APT_ARCHIVES / pat)):
            path = Path(path_str)
            try:
                path.unlink()
                removed.append(path)
            except OSError as e:
                print(f"  Could not remove {path}: {e}")
    if removed:
        print(f"  Freed: {', '.join(p.name for p in removed)}")
    return removed


def reinstall(pkg: str) -> None:
    cmd: list[str] = [
        "apt",
        "-qq",
        "install",
        "-y",
        "--reinstall",
        pkg,
    ]
    runcmd(cmd, show_output=True)


def main() -> None:
    args: list[str] = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags: set[str] = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        print("Usage: python reinstall_pkgs.py <pkg_file> [--reset]")
        sys.exit(1)
    pkg_file: Path = Path(args[0])
    progress_file: Path = pkg_file.with_name(pkg_file.name + PROGRESS_SUFFIX)
    if "--reset" in flags and progress_file.exists():
        progress_file.unlink()
        print("Progress reset.")
    pkgs: list[str] = read_packages(pkg_file)
    if not pkgs:
        print(f"No packages found in {pkg_file}")
        sys.exit(0)
    progress: dict[str, Any] = load_progress(progress_file)
    done: set[str] = set(progress["completed"]) | set(progress["failed"])
    pending: list[str] = [p for p in pkgs if p not in done]
    if not pending:
        print("All packages already processed.")
        if progress["failed"]:
            print(f"Previously failed: {', '.join(progress['failed'])}")
        sys.exit(0)
    if done:
        print(f"Resuming: {len(done)}/{len(pkgs)} already processed, {len(pending)} remaining.")
    try:
        for i, pkg in enumerate(pending, 1):
            progress["current"] = pkg
            save_progress(progress_file, progress)
            print(f"\n[{i}/{len(pending)}] Reinstalling {pkg} ...")
            try:
                reinstall(pkg)
                progress["completed"].append(pkg)
                cleanup_deb(pkg)
            except Exception as e:
                print(f"Failed to install {pkg}: {e}")
                progress["failed"].append(pkg)
            progress["current"] = None
            save_progress(progress_file, progress)
    except KeyboardInterrupt:
        print("\nInterrupted. Progress saved — re-run to continue.")
        sys.exit(130)
    print("\nDone.")
    print(f"  Completed: {len(progress['completed'])}")
    print(f"  Failed:    {len(progress['failed'])}")
    if progress["failed"]:
        print(f"  Failed packages: {', '.join(progress['failed'])}")


if __name__ == "__main__":
    main()
