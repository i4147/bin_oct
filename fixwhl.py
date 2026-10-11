#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that tells another AI coding agent how to reproduce a Python script that restores original wheel filenames by reading each wheel's METADATA, with the following requirements.

Build a Python 3 command-line utility (no code snippets needed in your output; implement it yourself) that restores proper wheel filenames for `.whl` files in a folder that were renamed to generic or incorrect names. The script must run on Termux (Android, shebang pointing to the Termux Python at `/data/data/com.termux/files/usr/bin/env python`) and should include `from __future__ import annotations`.

**Purpose:** Given a folder containing wheel files, read each wheel's internal `.dist-info/METADATA` file to determine its true distribution name and version, then rename the wheel to the standard form `{dist}-{version}-{tags}.whl`, preserving the original wheel's trailing tag portion when it can be derived from the existing filename.

**Dependencies:** Standard library only (`zipfile`, `pathlib`, `email.parser.Parser`, `collections.defaultdict`), plus the third-party `packaging` library for `packaging.utils.canonicalize_name`.

**Components to implement:**

1. `parse_metadata_from_wheel(wheel_path: Path)` — Open the wheel as a zip archive. Find the first entry whose name ends with `.dist-info/METADATA`; if none exists, raise `ValueError` with the message "missing .dist-info/METADATA". Decode its bytes as UTF-8 using `errors="replace"`, parse with the email `Parser`, and read the `Name` and `Version` headers. If either is missing or empty, raise `ValueError` ("missing Name or Version in METADATA"). Return a tuple of the canonicalized distribution name with hyphens replaced by underscores, and the raw version string.

2. `safe_target_path(dest: Path)` — If `dest` does not exist, return it unchanged. Otherwise, generate `{stem}.{i}{suffix}` candidates in the same directory with `i` starting at 1 and incrementing until a non-existing path is found, and return that path.

3. `restore_wheel_names(folder: str | Path)` — Convert the argument to a `Path`. Create a subdirectory named `_wheel_name_conflicts` inside it (tolerating an existing directory). Process all `.whl` files in the folder, grouping them by distribution name and version using a `defaultdict` so that multiple wheels resolving to the same name/version can be detected and handled (e.g., duplicates moved into the conflicts directory rather than overwritten). For each wheel: parse its metadata, derive the new filename from the distribution, version, and the original tag suffix; if the target name equals the current name, skip; otherwise rename to a path obtained through `safe_target_path` so nothing is overwritten. Wheels whose metadata cannot be read should be handled gracefully (report and continue, not crash the whole run).

**Main entry:** When executed as a script, call `restore_wheel_names` on a folder argument supplied on the command line (use `sys.argv`, with a sensible usage message if missing), and print a short summary of renamed, skipped, and conflicting files.

**Edge cases and behavior to preserve:** case and punctuation normalization in package names; a version string containing characters that are invalid in filenames should be left as-is in metadata but sanitized or handled safely in filenames; a non-existent folder should produce a clear error; non-zip or corrupt `.whl` files must be caught and reported without aborting; existing target names must never be overwritten; the conflicts directory should be created even when nothing ends up in it.

**Output expectations:** Produce a complete, runnable single-file script with type hints, concise docstrings, error handling that prints messages to stderr, and a `if __name__ == "__main__":` guard. Use `pathlib` for all path operations.
---"""

from __future__ import annotations

from collections import defaultdict
from email.parser import Parser
from pathlib import Path
from zipfile import ZipFile

from packaging.utils import canonicalize_name


def parse_metadata_from_wheel(wheel_path: Path):
    with ZipFile(wheel_path) as zf:
        meta_name = next(
            (n for n in zf.namelist() if n.endswith(".dist-info/METADATA")),
            None,
        )
        if meta_name is None:
            msg = "missing .dist-info/METADATA"
            raise ValueError(msg)
        text = zf.read(meta_name).decode("utf-8", errors="replace")
        msg = Parser().parsestr(text)
        name = msg.get("Name")
        version = msg.get("Version")
        if not name or not version:
            msg_0 = "missing Name or Version in METADATA"
            raise ValueError(msg_0)
        dist = canonicalize_name(name).replace("-", "_")
        return dist, version


def safe_target_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    i = 1
    while True:
        candidate = dest.with_name(f"{dest.stem}.{i}{dest.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def restore_wheel_names(folder: str | Path) -> None:
    folder = Path(folder)
    conflict_dir = folder / "_wheel_name_conflicts"
    conflict_dir.mkdir(exist_ok=True)
    versions_by_pkg = defaultdict(set)
    for src in sorted(folder.iterdir()):
        if not src.is_file() or src.suffix != ".whl":
            continue
        try:
            dist, version = parse_metadata_from_wheel(src)
            versions_by_pkg[dist].add(version)
        except Exception as e:
            print(f"SKIP  {src.name}  ({e})")
            continue
        dest = folder / f"{dist}-{version}-py3-none-any.whl"
        if dest.exists() and dest.resolve() != src.resolve():
            moved = safe_target_path(conflict_dir / src.name)
            src.rename(moved)
            print(f"CONFLICT {src.name} -> moved to {moved.name}")
        elif dest.resolve() == src.resolve():
            print(f"OK    {src.name} -> already correct")
        else:
            src.rename(dest)
            print(f"RENAMED {src.name} -> {dest.name}")
    for pkg, versions in sorted(versions_by_pkg.items()):
        if len(versions) > 1:
            print(f"MULTIPLE VERSIONS: {pkg} -> {sorted(versions)}")


if __name__ == "__main__":
    restore_wheel_names(".")
