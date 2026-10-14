#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a given directory tree for symbolic links and replaces each eligible symlink with a real copy of its target, so the directory becomes self-contained. The tool should accept a root directory path as input and process all symlinks beneath it in parallel using a bounded number of worker processes (around eight by default). For each symlink, it should resolve the target whether the link is absolute or relative to the link's location. Symlinks that point to files or directories should be replaced by a full copy of the target (directories copied recursively, files copied with metadata preserved), after the original link is removed. Skip symlinks that are special cases the user would not want touched: links located in a "bin" directory that point to a sibling in the same directory, and links pointing to shared library files with a ".so" extension. If a symlink's target no longer exists, record an error rather than failing the run. Log successfully replaced links to a file named "replaced.txt" in the output or working location, and log all failures and broken links to a file named "errors.txt". Use a logging facility that reports progress and warnings to the console as well. The script should print a concise summary at the end showing how many links were replaced, skipped, and failed. It should handle unexpected exceptions per item without aborting the entire batch, and it should be safe to run as a standalone command-line tool with clear usage guidance if the input path is missing or invalid.
---"""

from __future__ import annotations
from multiprocessing.pool import Pool
from pathlib import Path
import shutil
from typing import Final, NamedTuple
from loguru import logger

MAX_WORKERS: Final[int] = 8
REPLACED_LOG_NAME: Final[str] = "replaced.txt"
ERRORS_LOG_NAME: Final[str] = "errors.txt"


class ProcessResult(NamedTuple):
    status: str
    msg: str


def process_symlink(symlink_path: Path) -> ProcessResult | None:
    try:
        raw_target: Path = symlink_path.readlink()
        target_path: Path = raw_target if raw_target.is_absolute() else (symlink_path.parent / raw_target).resolve()
        if symlink_path.parent.name == "bin" and target_path.parent == symlink_path.parent:
            return None
        if target_path.suffix == ".so":
            return None
        if not target_path.exists():
            return ProcessResult(
                "error",
                f"Target does not exist: {symlink_path} -> {target_path}",
            )
        symlink_path.unlink()
        if target_path.is_dir():
            shutil.copytree(target_path, symlink_path)
        else:
            shutil.copy2(target_path, symlink_path)
        return ProcessResult(
            "replaced",
            f"Replaced: {symlink_path} -> {target_path}",
        )
    except Exception as e:
        return ProcessResult(
            "error",
            f"Failed to process {symlink_path}: {e!s}",
        )


def main() -> None:
    current_dir: Path = Path.cwd()
    replaced_log: Path = current_dir / REPLACED_LOG_NAME
    errors_log: Path = current_dir / ERRORS_LOG_NAME
    logger.info("Scanning for symlinks...")
    symlinks: list[Path] = [p for p in current_dir.rglob("*") if p.is_symlink()]
    if not symlinks:
        logger.info("No symlinks found.")
        return
    logger.info("Found {} symlinks. Processing in parallel...", len(symlinks))
    replaced_list: list[str] = []
    errors_list: list[str] = []
    with Pool(processes=MAX_WORKERS) as pool:
        for result in pool.imap_unordered(process_symlink, symlinks):
            if result is None:
                continue
            if result.status == "replaced":
                replaced_list.append(result.msg)
            elif result.status == "error":
                errors_list.append(result.msg)
    if replaced_list:
        replaced_log.write_text("\n".join(replaced_list) + "\n", encoding="utf-8")
        logger.info(
            "Successfully replaced {} symlinks. Logged to {}",
            len(replaced_list),
            REPLACED_LOG_NAME,
        )
    if errors_list:
        errors_log.write_text("\n".join(errors_list) + "\n", encoding="utf-8")
        logger.error(
            "Encountered {} errors. Logged to {}",
            len(errors_list),
            ERRORS_LOG_NAME,
        )


if __name__ == "__main__":
    raise SystemExit(main())
