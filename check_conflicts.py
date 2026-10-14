#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current Python environment for installed packages and detects naming conflicts between local module files and standard or third-party package names. The tool should accept an optional path to a JSON file containing a list of known PyPI package names (with a sensible default location) and an optional output path for a conflict report (defaulting to a JSON file in the current directory). If the PyPI name list is missing, it should print a warning to stderr and continue with the remaining checks rather than failing.
The script should gather the set of standard library module names, the names of all installed distributions (normalizing names so that hyphens, underscores, and dots are treated equivalently and comparisons are case-insensitive), and the names of the known PyPI packages. It should then examine the project's Python files and flag any local module or package whose name shadows a standard library module, an installed distribution, or a known PyPI package, since such shadowing can cause import errors or unexpected behavior.
For each detected conflict, record the local file path, the conflicting name, the category of conflict (standard library, installed, or PyPI), and a brief suggested remediation such as renaming the file. Write the complete results to the report file in a structured JSON format that includes a timestamp, the total counts of files scanned and conflicts found, and the list of individual conflicts. Print a concise human-readable summary to the console, and exit with a non-zero status code when conflicts are found so the tool can be used in automated checks. Handle unreadable files, malformed JSON input, and missing packages gracefully with clear error messages, and make the tool runnable from the command line with helpful usage information.
---"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import time
from dh import STDLIB

PIP_JSON = Path("/sdcard/data/pip.json")
DEFAULT_REPORT = Path("conflict_report.json")


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).strip().lower()


def load_pypi_names(path: Path) -> set[str]:
    if not path.exists():
        print(f"warning: {path} not found -- PyPI check skipped", file=sys.stderr)
        return set()
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    names: set[str] = set()
    for rec in data:
        if isinstance(rec, (list, tuple)) and rec:
            names.add(normalize(str(rec[0])))
        elif isinstance(rec, str):
            names.add(normalize(rec))
    return names


def installed_distributions() -> set[str]:
    try:
        from importlib.metadata import distributions
    except ImportError:
        from importlib_metadata import distributions
    names: set[str] = set()
    for dist in distributions():
        try:
            raw = dist.metadata["Name"]
        except Exception:
            raw = None
        if raw:
            names.add(normalize(str(raw)))
    return names


def collect_targets(root: Path):
    for p in sorted(root.iterdir()):
        if p.is_file() and p.suffix == ".py":
            yield p, p.stem, "module"
        elif p.is_dir() and (p / "__init__.py").is_file():
            yield p, p.name, "package"


def unique_target(path: Path) -> Path:
    stem, suffix = path.stem, path.suffix
    n = 1
    while True:
        candidate = path.with_name(f"{stem}_{n}{suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Detect and optionally fix filename conflicts with stdlib / PyPI packages.",
    )
    ap.add_argument(
        "-a",
        "--autofix",
        action="store_true",
        help="rename conflicting files by inserting '_N' before the extension",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_REPORT,
        help=f"path of the JSON report (default: {DEFAULT_REPORT})",
    )
    ap.add_argument(
        "-d",
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="directory to scan (default: current directory)",
    )
    ap.add_argument(
        "-i",
        "--installed-only",
        action="store_true",
        help="only report PyPI conflicts for packages installed in this interpreter (stdlib check is unaffected)",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    root: Path = args.dir.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    stdlib_lookup: dict[str, str] = {}
    for n in STDLIB:
        stdlib_lookup.setdefault(normalize(n), n)
    pypi = load_pypi_names(PIP_JSON)
    if args.installed_only:
        installed = installed_distributions()
        pypi &= installed
    conflicts: list[dict] = []
    checked = 0
    for path, import_name, kind in collect_targets(root):
        checked += 1
        key = normalize(import_name)
        real = stdlib_lookup.get(key)
        if real is not None:
            conflicts.append({
                "type": "stdlib",
                "path": str(path),
                "filename": path.name,
                "import_name": import_name,
                "shadows": real,
                "kind": kind,
            })
            continue
        if key in pypi:
            conflicts.append({
                "type": "pypi",
                "path": str(path),
                "filename": path.name,
                "import_name": import_name,
                "shadows": import_name,
                "kind": kind,
            })
    renamed = 0
    if args.autofix:
        for c in conflicts:
            old = Path(c["path"])
            if not old.exists():
                c["fixed"] = False
                c["fix_error"] = "source disappeared"
                continue
            new = unique_target(old)
            try:
                old.rename(new)
                c["fixed"] = True
                c["new_path"] = str(new)
                c["new_filename"] = new.name
                renamed += 1
            except OSError as e:
                c["fixed"] = False
                c["fix_error"] = str(e)
    else:
        for c in conflicts:
            c["fixed"] = False
    report = {
        "scanned_dir": str(root),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "autofix": args.autofix,
        "installed_only": args.installed_only,
        "checked": checked,
        "total_conflicts": len(conflicts),
        "renamed": renamed,
        "conflicts": conflicts,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Scanned {checked} importable item(s) in {root}")
    if args.installed_only:
        print("PyPI filter: installed-only")
    print(f"Report written to {args.output}")
    if not conflicts:
        print("OK: no filename conflicts detected.")
        return 0
    print(f"\nFound {len(conflicts)} conflict(s):")
    for c in conflicts:
        tag = f"[{c['type']}]"
        line = f"  {tag:<8} {c['filename']:<35} shadows {c['kind']} '{c['shadows']}'"
        if args.autofix and c.get("fixed"):
            line += f"  ->  {c['new_filename']}"
        elif args.autofix and not c.get("fixed"):
            line += f"  (fix failed: {c.get('fix_error', '?')})"
        print(line)
    if args.autofix:
        print(f"\nRenamed {renamed}/{len(conflicts)} item(s).")
    else:
        print("\nRun with -a / --autofix to rename them.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
