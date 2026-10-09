#!/data/data/com.termux/files/usr/bin/python

import shutil
from pathlib import Path


def find_whl(subdir: Path):
    """Return the first .whl file found in subdir or subdir/dist, or None."""
    # Look in subdir root first, then in dist/
    for location in (subdir, subdir / "dist"):
        if location.is_dir():
            for whl in location.glob("*.whl"):
                return whl
    return None


def clean_subdir(subdir: Path) -> None:
    whl = find_whl(subdir)

    if whl is None:
        print(f"[skip]  {subdir.name}: no .whl file")
        return

    # Move the whl to the subdir root if it's currently in dist/
    target = subdir / whl.name
    if whl.parent != subdir:
        shutil.move(str(whl), str(target))
        print(f"[move]  {whl.relative_to(subdir)} -> {target.name}")

    # Remove everything else inside subdir
    for entry in subdir.iterdir():
        if entry.resolve() == target.resolve():
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()
        print(f"[rm]    {subdir.name}/{entry.name}")

    print(f"[done]  {subdir.name}: kept {target.name}")


def main() -> None:
    cwd = Path.cwd()
    subdirs = [p for p in cwd.iterdir() if p.is_dir() and not p.name.startswith(".")]

    if not subdirs:
        print("No top-level subdirectories found.")
        return

    for subdir in subdirs:
        clean_subdir(subdir)


if __name__ == "__main__":
    main()
