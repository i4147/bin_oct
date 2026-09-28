#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that scans all files recursively from the current working directory (excluding symlinks and any paths inside ".git" folders), groups filenames by their file size using a helper "gsz" function from a local "dh" module, and sorts the resulting size groups in ascending order.
For each size that has more than one associated file, it prints the size highlighted in cyan (via the "cprint" helper from "dh") followed by an indented list of the matching filenames, effectively helping identify potential duplicate files based on matching sizes.
The script has no external inputs beyond the current directory contents and produces console output only, running via a "main" function invoked through the standard "if __name__ == '__main__'" entry point."""

from pathlib import Path
from dh import cprint, gsz
def main() -> None:
    root = Path.cwd()
    kp = {}
    files = [
        p
        for p in root.rglob("*")
        if p.is_file() and p.exists() and not p.is_symlink() and ".git" not in p.parts
    ]
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