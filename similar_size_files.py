#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory recursively and reports groups of files that share the exact same size, helping the user spot potential duplicates. The script should skip any files located inside version-control metadata folders (such as `.git`) and ignore symbolic links and non-regular entries. It should gather every regular file, group them by byte size, and then output only the size groups that contain two or more files. Results should be presented in ascending order of file size, with each size shown as a clearly highlighted header followed by an indented list of the matching file names. Files with a unique size should not appear in the output. The tool should run as a command-line program with no required arguments, use colored terminal output for the size headers if available, and exit cleanly with a status code when finished. Handle file access errors gracefully so that an unreadable file does not crash the whole scan.
---"""

from __future__ import annotations
from pathlib import Path
from dh import cprint, gsz


def main() -> None:
    root = Path.cwd()
    kp = {}
    files = [p for p in root.rglob("*") if p.is_file() and p.exists() and not p.is_symlink() and ".git" not in p.parts]
    for f in files:
        path = Path(root / f)
        psz = gsz(path)
        kp.setdefault(psz, []).append(path.name)
    orig = kp
    kz = sorted(kp.keys())
    pk = {}
    for x in kz:
        pk[x] = orig.get(x)
    for k, v in pk.items():
        if len(v) > 1:
            cprint(f"{k}:", "cyan")
            for i in v:
                print(f"    - {i}")


if __name__ == "__main__":
    raise SystemExit(main())
