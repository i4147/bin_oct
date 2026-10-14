#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory for Python package projects (directories containing a setup.py, pyproject.toml, or setup.cfg file), builds a wheel for each one in parallel using a fixed-size pool of worker processes, and collects all build artifacts into a single output folder named "wheels" within the current directory, creating that folder if it does not already exist. The script should skip the output folder itself when looking for packages, and should print a clear message and exit gracefully if no packages are found.
Each build should be run as an isolated external process using the current Python interpreter and the standard build tooling for producing wheel distributions. For every package, record whether the build succeeded, and if it failed, capture the tail end of the error output so the user can diagnose the problem. Exceptions raised during a build should be caught and reported without stopping the other builds.
When all builds finish, print a concise summary to the console showing each package name with its status (success or failure, along with the error excerpt for failures), followed by totals of successful and failed builds. Packages should be processed in a deterministic, alphabetical order. The script should be runnable directly from the command line, with the main logic placed behind a standard entry-point guard, and should handle the multiprocessing setup correctly across platforms.
---"""

from __future__ import annotations
from multiprocessing import Pool
from pathlib import Path
import subprocess
import sys

NUM_WORKERS = 8
CURRENT_DIR = Path.cwd()
OUTPUT_DIR = CURRENT_DIR / "wheels"


def is_package_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    return (path / "setup.py").exists() or (path / "pyproject.toml").exists() or (path / "setup.cfg").exists()


def build_wheel(pkg_dir: Path) -> tuple[str, bool, str]:
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--outdir",
                str(OUTPUT_DIR),
                str(pkg_dir),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return (pkg_dir.name, True, "OK")
        else:
            return (pkg_dir.name, False, result.stderr.strip()[-500:])
    except Exception as e:
        return (pkg_dir.name, False, f"Exception: {e}")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    pkg_dirs = sorted(p for p in CURRENT_DIR.iterdir() if is_package_dir(p) and p != OUTPUT_DIR)
    if not pkg_dirs:
        print("No package directories found in", CURRENT_DIR)
        return
    print(f"Found {len(pkg_dirs)} package(s):")
    for p in pkg_dirs:
        print("  -", p.name)
    print(f"\nBuilding wheels into: {OUTPUT_DIR}")
    print(f"Using {NUM_WORKERS} workers\n")
    results = []
    with Pool(processes=NUM_WORKERS) as pool:
        async_results = [(pkg_dir, pool.apply_async(build_wheel, (pkg_dir,))) for pkg_dir in pkg_dirs]
        for pkg_dir, ar in async_results:
            name, ok, msg = ar.get()
            status = "✓" if ok else "✗"
            print(f"[{status}] {name}: {msg if not ok else 'built'}")
            results.append((name, ok))
    success = sum(1 for _, ok in results if ok)
    failed = len(results) - success
    print(f"\nDone. Success: {success}, Failed: {failed}")


if __name__ == "__main__":
    main()
