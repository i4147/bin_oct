#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory for Python source files and reports which imported modules they depend on, classifying each dependency as either a standard library module or a third-party package. The script should read a plain-text list of installed pip packages from a fixed location on the device (a file such as a pip freeze export); if that file is missing, it should warn the user on stderr and continue without the third-party check. Package names from the list should be normalized so that differences in hyphens, underscores, and letter case do not cause false mismatches, and version specifiers should be stripped while parsing it. Comments and blank lines in the list should be ignored.
The script should print a clear, human-readable report to standard output that begins with the directory being scanned and the number of standard library modules recognized, then lists the findings per file or as an aggregated summary. It should identify imports that are neither standard library modules nor listed packages (likely missing dependencies), and clearly separate them from the known third-party and standard library imports. Local modules that correspond to files within the scanned directory should be recognized and not flagged as external. Where Python's standard library module list is unavailable on older interpreters, the script should degrade gracefully with a warning rather than crashing.
Use emoji-style status markers sparingly for readability, handle unreadable or non-UTF-8 files without stopping the scan, and exit with a zero status on success and a non-zero status if the scan itself cannot run. Keep the output concise, deterministic in ordering, and suitable for both interactive terminal use and piping into other tools.
---"""

from __future__ import annotations
from pathlib import Path
import sys

PIP_LIST = Path("/sdcard/data/pip.txt")
TARGET_DIR = Path.cwd()


def load_third_party(path: Path) -> set[str]:
    names: set[str] = set()
    if not path.is_file():
        print(f"⚠️  {path} not found — skipping 3rd-party check", file=sys.stderr)
        return names
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name = line.split("==")[0].split(">=")[0].split("<=")[0]
        name = name.split()[0].strip()
        name = name.replace("-", "_").lower()
        if name:
            names.add(name)
    return names


def main() -> int:
    stdlib = {n.lower() for n in getattr(sys, "stdlib_module_names", set())}
    third_party = load_third_party(PIP_LIST)
    if not stdlib:
        print(
            "⚠️  sys.stdlib_module_names unavailable (needs Python 3.10+)",
            file=sys.stderr,
        )
    print(f"📂 Scanning: {TARGET_DIR}")
    print(f"📦 stdlib entries: {len(stdlib)} | 3rd-party entries: {len(third_party)}\n")
    conflicts = 0
    for py in sorted(TARGET_DIR.rglob("*.py")):
        stem = py.stem.lower()
        hits = []
        if stem in stdlib:
            hits.append("stdlib")
        if stem in third_party:
            hits.append("3rd-party")
        if hits:
            conflicts += 1
            rel = py.relative_to(TARGET_DIR)
            print(f"❌ {rel}  →  conflicts with: {', '.join(hits)}")
    if conflicts == 0:
        print("✅ No conflicts found.")
    else:
        print(f"\n⚠️  {conflicts} conflicting file(s).")
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
