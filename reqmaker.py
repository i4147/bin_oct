#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans up a project's requirements file by using pip's dependency checker to detect and resolve missing-dependency problems. The script should read a requirements.txt file in the current directory, run a pip consistency check on the current environment, and parse its output to identify which installed packages are missing dependencies that other packages declare. It should then add the missing dependencies to the requirements file, while skipping any packages on a predefined exclusion list of heavy or problematic libraries (such as large machine learning, scientific computing, and browser automation packages) so they are never auto-added. The script should avoid duplicate entries, keep the requirements file clean and sorted, and write the updated list back to disk. It should report to the user, in readable form, which dependencies were detected as missing, which were added, and which were skipped due to the exclusion list. The script should handle the case where the requirements file does not yet exist, handle pip failures gracefully (including non-zero exit codes whose output is still useful), and make no changes if no new packages need to be added. The overall goal is to make the requirements file complete and consistent with the packages actually needed by the environment, with a clear command-line experience and safe, idempotent behavior when run repeatedly.
---"""

from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import re
import subprocess
import sys

REQ = Path("requirements.txt")
BLACKLIST = {
    "pydantic-core",
    "h5py",
    "jiter",
    "jupyter-server-ydoc",
    "scipy",
    "rpds-py",
    "nh3",
    "pandas",
    "torch",
    "torchvision",
    "scikit-learn",
    "pynacl",
    "gensim",
    "spacy",
    "torchaudio",
    "selenium",
    "jupyter-ydoc",
    "tensorflow",
}


def save_to_req(packages) -> None:
    REQ.write_text("\n".join(packages) + "\n", encoding="utf-8")


def run_pip_check():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip() if e.stdout else ""


def parse_pip_check(output):
    pattern = re.compile(r"^(\S+)\s+.*requires\s+([^,]+),\s+which is not installed\.$", re.MULTILINE)
    missing_deps = defaultdict(list)
    for line in output.splitlines():
        match = pattern.match(line.strip())
        if match:
            requirer = match.group(1)
            missing_pkg = match.group(2).strip()
            if missing_pkg in BLACKLIST:
                continue
            missing_deps[missing_pkg].append(requirer)
    return missing_deps


def format_deptree(missing_deps) -> None:
    if not missing_deps:
        print("No missing dependencies found.")
        return
    print("required packages:")
    for pkg, requirers in sorted(missing_deps.items()):
        unique_requirers = sorted(set(requirers))
        requirers_str = ", ".join(unique_requirers)
        print(f"  - {pkg} --> {requirers_str}")


def main() -> None:
    output = run_pip_check()
    if not output:
        print("No output from `pip check`. Are you in a virtual environment?")
        return
    missing_deps = parse_pip_check(output)
    format_deptree(missing_deps)
    save_to_req(sorted(missing_deps.keys()))


if __name__ == "__main__":
    raise SystemExit(main())
