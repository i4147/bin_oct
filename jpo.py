#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations

import argparse
import multiprocessing as mp
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

JPEG_EXTS = {".jpg", ".jpeg"}
SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__", "lazy"}
GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"


@dataclass
class Result:
    path: Path
    before: int
    after: int
    status: str
    detail: str = ""

    @property
    def saved(self) -> int:
        return max(self.before - self.after, 0)


def walk_jpegs(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = dirpath / name
            if p.suffix.lower() in JPEG_EXTS and not p.is_symlink() and p.is_file():
                yield p


def optimize_one(args: tuple[Path, int, bool]) -> Result:
    path, quality, dry_run = args
    try:
        before = path.stat().st_size
    except OSError as e:
        return Result(path, 0, 0, "error", str(e))

    cmd = ["jpegoptim", f"-m{quality}", "--strip-all", "-q"]
    cmd.append("-t" if dry_run else "-o")
    cmd.append(str(path))

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return Result(path, before, before, "error", "jpegoptim not found")

    if proc.returncode != 0:
        return Result(path, before, before, "error", (proc.stderr or proc.stdout).strip()[:200])

    if dry_run:
        return Result(path, before, before, "unchanged")

    after = path.stat().st_size
    if after >= before:
        return Result(path, before, after, "unchanged")
    return Result(path, before, after, "optimized")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-j", "--jobs", type=int, default=4)
    ap.add_argument("-q", "--quality", type=int, default=70)
    ap.add_argument("-n", "--dry-run", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    if not shutil.which("jpegoptim"):
        print("Error: jpegoptim not found in PATH.", file=sys.stderr)
        return 1

    root = Path(args.root).resolve()
    files = list(walk_jpegs(root))
    if not files:
        print(f"No JPEGs found under {root}")
        return 0

    print(f"Root: {root}")
    print(
        f"Files: {len(files)} | Quality: {args.quality} | "
        f"strip-all | skip-if-larger | jobs: {args.jobs} | dry-run: {args.dry_run}"
    )
    print("-" * 60)

    tasks = [(p, args.quality, args.dry_run) for p in files]
    total_saved = 0
    optimized = unchanged = errors = 0

    with mp.Pool(processes=args.jobs) as pool:
        for r in pool.imap_unordered(optimize_one, tasks):
            if r.status == "optimized":
                optimized += 1
                total_saved += r.saved
                print(f"{r.path.name} {GREEN}{r.saved}{RESET}")
            elif r.status == "unchanged":
                unchanged += 1
                print(f"{r.path.name} {DIM}unchanged{RESET}")
            else:
                errors += 1
                print(f"{r.path.name} {DIM}error: {r.detail}{RESET}", file=sys.stderr)

    print("-" * 60)
    if args.dry_run:
        print(f"Dry run complete. {len(files)} files scanned.")
    else:
        print(f"Optimized: {optimized} | Unchanged: {unchanged} | Errors: {errors}")
        print(f"Space freed: {GREEN}{total_saved:,} bytes{RESET} ({total_saved / 1024 / 1024:.2f} MiB)")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
