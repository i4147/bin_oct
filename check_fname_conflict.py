#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 script (intended for Termux on Android, shebang pointing to Termux's Python) that scans the current working directory recursively for `.py` files and reports any file whose name (stem) collides with a Python standard library module name or a third-party package name listed in a pip requirements-style text file.

Requirements for the script:

**Purpose:** Detect local Python filenames that would shadow stdlib or installed third-party modules during import, causing hard-to-diagnose import errors.

**Configuration:** Use two module-level constants: a path to a pip list file at `/sdcard/data/pip.txt`, and the scan target set to the current working directory at startup. Use `pathlib.Path` throughout.

**Inputs:**
- A pip-style text file (UTF-8, decoding errors ignored). Each non-empty line not starting with `#` is a requirement. Strip version specifiers (`==`, `>=`, `<=`), take the first whitespace-separated token, replace hyphens with underscores, and lowercase it. Collect results into a set of names.
- The directory tree under the current working directory, searched recursively for `*.py` files, processed in sorted order.

**Helper function `load_third_party(path)`:** Returns a set of normalized names. If the file does not exist, print a warning to stderr (with a warning emoji, mentioning the path and that the third-party check is being skipped) and return an empty set. Ignore blank lines and comments.

**Main function `main()`, returns an int exit status:**
1. Build the stdlib set from `sys.stdlib_module_names` (via `getattr` with an empty-set default), lowercased. If it is empty, print a stderr warning stating it requires Python 3.10+.
2. Load the third-party set.
3. Print the scanned directory and counts of stdlib and third-party entries, formatted as "📂 Scanning: <dir>" and "📦 stdlib entries: N | 3rd-party entries: M" followed by a blank line.
4. For each `.py` file, take its stem lowercased. Collect a list of hits: "stdlib" if the stem is in the stdlib set, "3rd-party" if it is in the third-party set. If there are hits, report the file (its path, the matched categories, and the conflict count) and increment a conflict counter. Preserve the original output style with emoji markers for each finding.
5. At the end, print a summary with the total conflict count and return a nonzero exit status when conflicts exist, zero otherwise.

**Behavior and edge cases:**
- Run `main()` under the standard `if __name__ == "__main__":` guard and exit with its return value via `sys.exit`.
- Matching is by file stem only, case-insensitive; directory names are not checked; `__init__` and similar names are treated like any other stem.
- Missing pip list file is non-fatal; the scan proceeds with stdlib-only checking.
- Python 3.10+ is needed for `sys.stdlib_module_names`; older versions still run but report no stdlib conflicts.
- Use only the standard library, no third-party dependencies.
- Use UTF-8 for reading files, with error-tolerant decoding.
- Output warnings and diagnostics to stderr, and normal reporting to stdout.
- Include type hints (e.g., `set[str]`, `-> int`) and a Termux-style shebang line for Android Python.

**Usage:** Run from the project root directory with `python <script>`; the exit code signals whether any shadowing conflicts were found, making it usable in CI or pre-commit checks.
---"""

import sys
from pathlib import Path

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
