#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a Python site-packages directory tree for folders named "tests" (test directories bundled inside installed packages) and relocates them into a separate destination directory while preserving each folder's original relative location within the package tree. The script should support a dry-run mode, enabled via a command-line flag, that reports every planned move without modifying the file system. Certain packages, such as numerical and data-science libraries (numpy, pandas, scipy, numba), must be skipped entirely, and any path that falls under them should be reported as excluded rather than moved. The source and destination locations should be sensible defaults but easily configurable. Processing should run concurrently with a bounded number of worker processes to speed up work across many directories. Each file-system operation should be handled defensively: failures for an individual folder (such as permission errors, missing destinations, or name collisions) must be captured and reported without aborting the whole run. Results for every candidate folder should be collected and summarized at the end, showing how many were moved, skipped as excluded, dry-run previews, and errors, with clear logging of progress and outcomes throughout.
---"""

from __future__ import annotations
from multiprocessing.pool import Pool
from pathlib import Path
import shutil
import sys
from typing import Final, NamedTuple
from loguru import logger

MAX_WORKERS: Final[int] = 8
SRC: Final[Path] = Path("/data/data/com.termux/files/usr/lib/python3.14/site-packages")
DEST: Final[Path] = Path.home() / "tmp" / "tests_dirs"
EXCLUDED: Final[tuple[str, ...]] = ("numpy", "pandas", "scipy", "numba")
DRY_RUN: Final[bool] = "-d" in sys.argv


class MoveResult(NamedTuple):
    path: Path
    success: bool
    message: str


def _is_excluded(path: Path) -> bool:
    parts: tuple[str, ...] = path.parts
    return any(name in parts for name in EXCLUDED)


def move_tests_folder(
    tests_path: Path,
    base_src: Path,
    base_dst: Path,
    dry_run: bool = DRY_RUN,
) -> MoveResult:
    if _is_excluded(tests_path):
        return MoveResult(tests_path, False, f"excluded path: {tests_path}")
    try:
        relative_path: Path = tests_path.relative_to(base_src)
        dst_path: Path = base_dst / relative_path.parent / tests_path.name
        if dry_run:
            return MoveResult(tests_path, True, f"will move: {tests_path} -> {dst_path}")
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tests_path), str(dst_path))
        return MoveResult(tests_path, True, f"moved: {tests_path} -> {dst_path}")
    except Exception as e:
        return MoveResult(tests_path, False, f"error moving {tests_path}: {e}")


def move_tests_recursive(
    source_dir: Path = SRC,
    destination_dir: Path = DEST,
    dry_run: bool = DRY_RUN,
) -> int:
    source: Path = source_dir.resolve()
    destination: Path = destination_dir
    tests_folders: list[Path] = [p for p in source.rglob("tests") if p.is_dir() and not _is_excluded(p)]
    if not tests_folders:
        logger.info("No 'tests' folders found.")
        return 0
    logger.info("Found {} 'tests' folder(s) to move", len(tests_folders))
    logger.info("Source: {}", source)
    logger.info("Destination: {}", destination)
    if not dry_run:
        destination.mkdir(parents=True, exist_ok=True)
    jobs: list[tuple[Path, Path, Path, bool]] = [
        (tests_path, source, destination, dry_run) for tests_path in tests_folders
    ]
    moved_count: int = 0
    with Pool(processes=MAX_WORKERS) as pool:
        for result in pool.starmap(move_tests_folder, jobs):
            if result.success:
                logger.info("{}", result.message)
                moved_count += 1
            else:
                logger.warning("{}", result.message)
    logger.info(
        "✓ Successfully moved {}/{} directories",
        moved_count,
        len(tests_folders),
    )
    return moved_count


def main() -> None:
    move_tests_recursive()


if __name__ == "__main__":
    raise SystemExit(main())
