#!/data/data/com.termux/files/usr/bin/python3.12
"""Create a Termux-compatible Python 3.12 command-line script for extracting RAR archives (including multi-part/split RAR archives) on Android/Termux systems.

Purpose:
The script should locate a RAR archive (or the first part of a multi-volume RAR set), determine all related volume files belonging to the same archive, compute a destination extraction directory derived from the archive's filename, and extract the archive's contents into that directory safely.

Main inputs:
- A path to a RAR archive file (e.g., "archive.rar", "archive.part1.rar", or "archive.part01.rar") provided as a command-line argument.

Main outputs:
- A new directory created next to the archive (named after the archive without its RAR/part suffix) containing the extracted files.
- Console output/logging indicating progress, success, or errors during extraction.
- Appropriate process exit codes reflecting success or failure.

Notable behavior and requirements:
1. Try to import the optional `libarchive` Python binding; if unavailable, gracefully fall back to using external command-line extraction tools. Track availability with a boolean flag (e.g., HAVE_LIBARCHIVE).
2. Define a fix  search for onATH: "unrar", "7z", "7za", "7zz", "bsdtar" (in that priority order).
3. Implement a function to find the first available extractor executable path on the system using `shutil.which`, returning None if none are found.
4. Implement a function that, given an archive Path, detects whether it is part of a multi-volume split RAR set by checking for filename suffixes ".part1.rar" or ".part01.rar" (case-insensitive). If so, scan the archive's parent directory and return a sorted list of all sibling files that share the same base name (case-insensitive) and end with ".rar", representing all volume parts. If the archive is not part of a detected multi-part set, return a single-element list containing just that archive.
5. Implement a function that computes the destination extraction directory from the archive path: strip known suffixes (".part1.rar", ".part01.rar", ".rar") case-insensitively from the filename to form the output directory name (sibling directory to the archive); if none of those suffixes match, fall back to using the path's stem (removing just the last suffix).
6. Implement a safe path-joining helper that prevents path traversal / zip-slip style vulnerabilities: given a destination directory and a relative entry name from the archive, resolve the combined path and verify it still lies within the resolved destination directory (using `relative_to`), returning None if the entry would escape the destination directory, or the resolved safe target Path otherwise.
7. Implement an extraction routine that uses the `libarchive` binding (when available) to read entries from the archive and extract them into the destination directory, creating the destination directory (with parents) if it doesn't exist, and applying the safe-join check to each entry before writing it to disk.
8. Include a fallback extraction path that invokes one of the external extractor executables (via `subprocess`) when `libarchive` is not available or fails, using the first extractor found by the extractor-search function.
9. Use `pathlib.Path` throughout for all filesystem path handling, and `sys` for command-line argument handling and exit codes.
10. The script should be structured as a standalone executable with a Termux-specific shebang line (`#!/data/data/com.termux/files/usr/bin/python3.12`) and use `from __future__ import annotations` for type hint compatibility.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/PEt6HkE3cu4H4PSVaw3jCv"""

from __future__ import annotations
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import libarchive

    HAVE_LIBARCHIVE = True
except ImportError:
    libarchive = None
    HAVE_LIBARCHIVE = False
EXTRACTORS = ("unrar", "7z", "7za", "7zz", "bsdtar")


def find_extractor() -> str | None:
    for cmd in EXTRACTORS:
        if path := shutil.which(cmd):
            return path
    return None


def archive_parts(archive: Path) -> list[Path]:
    lower = archive.name.lower()
    for suffix in (".part1.rar", ".part01.rar"):
        if lower.endswith(suffix):
            base = archive.name[: -len(suffix)].lower()
            return sorted(
                p
                for p in archive.parent.iterdir()
                if p.is_file() and p.name.lower().startswith(base) and p.name.lower().endswith(".rar")
            )
    return [archive]


def dest_dir(archive: Path) -> Path:
    name = archive.name
    lower = name.lower()
    for suffix in (".part1.rar", ".part01.rar", ".rar"):
        if lower.endswith(suffix):
            return archive.with_name(name[: -len(suffix)])
    return archive.with_suffix("")


def safe_join(dest: Path, name: str) -> Path | None:
    resolved_dest = dest.resolve()
    target = (dest / name).resolve()
    try:
        target.relative_to(resolved_dest)
    except ValueError:
        return None
    return target


def extract_libarchive(archive: Path, dest: Path) -> bool:
    dest.mkdir(parents=True, exist_ok=True)
    try:
        with libarchive.file_reader(str(archive)) as reader:
            for entry in reader:
                out = safe_join(dest, entry.pathname)
                if out is None:
                    print(
                        f"  ! skipping unsafe path: {entry.pathname}",
                        file=sys.stderr,
                    )
                    continue
                if entry.isdir:
                    out.mkdir(parents=True, exist_ok=True)
                    continue
                out.parent.mkdir(parents=True, exist_ok=True)
                with open(out, "wb") as f:
                    f.writelines(entry.get_blocks())
        return True
    except Exception as e:
        print(f"  ! libarchive failed: {e}", file=sys.stderr)
        shutil.rmtree(dest, ignore_errors=True)
        return False


def extract_subprocess(archive: Path, extractor: str, dest: Path) -> bool:
    dest.mkdir(parents=True, exist_ok=True)
    exe = Path(extractor).name
    if exe.startswith("unrar"):
        args = [extractor, "x", "-o+", "-y", str(archive), str(dest) + "/"]
    elif exe.startswith("7z"):
        args = [extractor, "x", "-y", f"-o{dest}", str(archive)]
    else:
        args = [extractor, "-xf", str(archive), "-C", str(dest)]
    try:
        subprocess.run(args, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        msg = (e.stderr or e.stdout or b"").decode(errors="replace").strip()
        print(f"  ! {exe} failed: {msg}", file=sys.stderr)
        shutil.rmtree(dest, ignore_errors=True)
        return False
    except OSError as e:
        print(f"  ! could not run {extractor}: {e}", file=sys.stderr)
        shutil.rmtree(dest, ignore_errors=True)
        return False


def extract(archive: Path, dest: Path, extractor: str | None) -> bool:
    if HAVE_LIBARCHIVE:
        if extract_libarchive(archive, dest):
            return True
        if extractor is None:
            return False
        print("  retrying via subprocess fallback...", file=sys.stderr)
    if extractor is None:
        print(
            "error: install libarchive-c or one of: " + ", ".join(EXTRACTORS),
            file=sys.stderr,
        )
        return False
    return extract_subprocess(archive, extractor, dest)


def main() -> int:
    extractor = find_extractor()
    if not HAVE_LIBARCHIVE and extractor is None:
        print(
            "error: install libarchive-c or one of: " + ", ".join(EXTRACTORS),
            file=sys.stderr,
        )
        return 1
    if HAVE_LIBARCHIVE:
        print("backend: libarchive")
    else:
        print(f"backend: subprocess ({Path(extractor).name})")
    root = Path.cwd()
    archives = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".rar")
    if not archives:
        print("No .rar archives found.")
        return 0
    handled: set[Path] = set()
    for archive in archives:
        if archive in handled:
            continue
        parts = archive_parts(archive)
        handled.update(parts)
        dest = dest_dir(archive)
        rel_arc = archive.relative_to(root)
        rel_dst = dest.relative_to(root)
        print(f"[+] {rel_arc}  ->  {rel_dst}/")
        if extract(archive, dest, extractor):
            removed = 0
            for part in parts:
                try:
                    part.unlink()
                    removed += 1
                except OSError as e:
                    print(
                        f"  ! could not remove {part.name}: {e}",
                        file=sys.stderr,
                    )
            print(f"  removed {removed} archive file(s)")
        else:
            print("  archive kept")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
