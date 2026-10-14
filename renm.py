#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a target directory (defaulting to the current directory) for files whose names contain non-English characters, translates each non-English file name (stem only, preserving the file extension) into English using an online translation service, and renames the files to their English equivalents. The tool should be parallelized across multiple worker processes to handle large numbers of files efficiently, and should offer a command-line interface allowing the user to specify the target directory, the number of workers, and the parallel execution strategy to use (such as map-based, starmap-based, unordered iterative, or asynchronous per-task execution).
Key behaviors:
- Leave files whose stems are already pure ASCII/English unchanged.
- Skip renaming when translation fails or produces an empty result, logging a warning instead of crashing.
- Ensure no filename collisions occur: if the translated name already exists, generate a unique alternative path rather than overwriting existing files.
- Sanitize translated names so they are valid file names on the operating system.
- Show progress feedback to the user while processing, and log each rename or skipped item with a clear, structured message.
- Return a summary of how many files were scanned, translated, renamed, and skipped or failed.
- Handle errors gracefully so that a single failing file does not stop the overall run.
- Include a dry-run option that reports the planned renames without modifying any files.
---"""

from __future__ import annotations
import argparse
from multiprocessing.pool import AsyncResult, Pool
import os
from pathlib import Path
import re
from typing import TYPE_CHECKING, Final, TypeAlias
from deep_translator import GoogleTranslator
from dh import unique_path
from loguru import logger
from tqdm import tqdm

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
DIRECTORY: Final[str] = "."
POOL_WORKERS: Final[int] = 8
POOL_METHODS: Final[tuple[str, ...]] = (
    "map",
    "starmap",
    "imap_unordered",
    "apply_async",
)
NON_ENGLISH_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^\x00-\x7F]")
NamePair: TypeAlias = tuple[str, str]


def walk_files(directory: str) -> Iterator[str]:
    for root, _dirs, files in os.walk(directory):
        for name in files:
            yield os.path.join(root, name)


def is_english(text: str) -> bool:
    return NON_ENGLISH_PATTERN.search(text) is None


def translate_name(name: str) -> NamePair:
    path = Path(name)
    stem = path.stem
    suffix = path.suffix
    if is_english(stem):
        return (name, name)
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(stem)
        if not translated:
            return (name, name)
        return (name, translated + suffix)
    except Exception as exc:
        logger.debug(f"Translation failed for '{stem}': {exc}")
        return (name, name)


def _translate_name_tuple(item: tuple[str]) -> NamePair:
    return translate_name(item[0])


def _run_pool(names: Sequence[str], method: str) -> list[NamePair]:
    with Pool(processes=POOL_WORKERS) as pool:
        if method == "map":
            return pool.map(_translate_name_tuple, [(name,) for name in names])
        if method == "starmap":
            return pool.starmap(translate_name, [(name,) for name in names])
        if method == "imap_unordered":
            return list(pool.imap_unordered(_translate_name_tuple, [(n,) for n in names]))
        if method == "apply_async":
            async_results: list[AsyncResult[NamePair]] = [pool.apply_async(translate_name, (name,)) for name in names]
            return [result.get() for result in async_results]
    msg = f"Unsupported pool method: {method}"
    raise ValueError(msg)


def _build_translation_map(paths: Sequence[Path], pool_method: str) -> dict[str, str]:
    unique_names: list[str] = sorted({path.name for path in paths if not is_english(path.name)})
    if not unique_names:
        return {}
    translation_map: dict[str, str] = {}
    for original, translated in tqdm(
        _run_pool(unique_names, pool_method),
        total=len(unique_names),
        desc="Translating filenames",
    ):
        translation_map[original] = translated
    return translation_map


def rename_files(directory: Path, pool_method: str) -> None:
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Not a directory: {directory}")
        return
    paths: list[Path] = [Path(p) for p in walk_files(str(directory))]
    if not paths:
        logger.info("No files found.")
        return
    translation_map = _build_translation_map(paths, pool_method)
    if not translation_map:
        logger.info("No non-English filenames found.")
        return
    for path in sorted(paths, key=lambda p: len(p.parts), reverse=True):
        new_name = translation_map.get(path.name)
        if new_name is None or new_name == path.name:
            continue
        new_path = unique_path(path.with_name(new_name))
        try:
            path.rename(new_path)
            logger.info(f"Renamed: {path.name} -> {new_path.name}")
        except OSError as exc:
            logger.error(f"Error renaming {path.name}: {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory",
        default=DIRECTORY,
        help="Directory to scan and rename.",
    )
    parser.add_argument(
        "--pool-method",
        choices=POOL_METHODS,
        default="map",
        help="Multiprocessing pool method to use for translation.",
    )
    return parser.parse_args()


def main() -> int:
    args: argparse.Namespace = parse_args()
    pool_method: str = args.pool_method
    directory: Path = Path(args.directory)
    rename_files(directory, pool_method)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
