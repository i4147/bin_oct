#!/data/data/com.termux/files/usr/bin/env python

from pathlib import Path


def flatten_only_children(root_dir: str | Path) -> list[tuple[Path, Path]]:
    root = Path(root_dir).resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    moves: list[tuple[Path, Path]] = []
    while True:
        moved_this_pass = False
        for subdir in list(root.iterdir()):
            if not subdir.is_dir():
                continue
            try:
                children = list(subdir.iterdir())
            except PermissionError:
                continue
            if len(children) != 1 or not children[0].is_dir():
                continue
            src = children[0]
            dst = root / src.name
            if dst.exists():
                print(f"[skip] {dst} already exists")
                continue
            src.rename(dst)
            print(f"[move] {src}  ->  {dst}")
            moves.append((src, dst))
            moved_this_pass = True
        if not moved_this_pass:
            break
    return moves


def remove_empty_subdirs(root_dir: str | Path) -> list[Path]:
    root = Path(root_dir).resolve()
    removed: list[Path] = []
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir():
            try:
                if not any(path.iterdir()):
                    path.rmdir()
                    print(f"[rm]   {path}")
                    removed.append(path)
            except PermissionError:
                pass
    return removed


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Flatten only-child subdirectory chains and remove empty dirs.")
    ap.add_argument("root", nargs="?", default=".", help="root directory (default: .)")
    args = ap.parse_args()
    flatten_only_children(args.root)
    remove_empty_subdirs(args.root)
