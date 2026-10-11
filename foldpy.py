#!/data/data/com.termux/files/usr/bin/python
"""I'm going to stop here, because the request has a problem I can't work around: the code you pasted is truncated mid-line (`futures = {exec`), so the full script isn't available for me to describe. I also won't reproduce any code in the prompt, per your instructions.

Could you paste the complete script? Once I have it, I'll write the self-contained prompt in English with no code snippets, covering purpose, inputs and outputs, dependencies, logic, error handling, edge cases, and usage.
---"""

import argparse
import ast
import shutil
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Literal, Tuple

from rich.progress import Progress

Status = Literal["ok", "error", "warn"]


def check_file(path: Path) -> tuple[Path, Status]:
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return path, "error"
    try:
        ast.parse(source, filename=str(path))
    except SyntaxError:
        return path, "error"
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            compile(source, str(path), "exec")
        except Exception:
            return path, "error"
        if any(issubclass(x.category, SyntaxWarning) for x in w):
            return path, "warn"
    return path, "ok"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--apply", action="store_true")
    args = parser.parse_args()

    cwd = Path.cwd()
    files = list(cwd.glob("*.py"))
    if not files:
        print("No .py files found.")
        return

    results: list[tuple[Path, Status]] = []
    with Progress() as progress:
        task = progress.add_task("Processing .py files", total=len(files))
        with ProcessPoolExecutor() as executor:
            futures = {executor.submit(check_file, f): f for f in files}
            for future in as_completed(futures):
                results.append(future.result())
                progress.update(task, advance=1)

    groups: dict[str, list[Path]] = {"ok": [], "error": [], "warn": []}
    for path, status in results:
        groups[status].append(path)

    for status, paths in groups.items():
        print(f"{status}: {len(paths)} files")
        for p in paths:
            print(f"  {p.name}")

    if args.apply:
        for status, paths in groups.items():
            if not paths:
                continue
            target_dir = cwd / status
            target_dir.mkdir(exist_ok=True)
            for p in paths:
                shutil.move(str(p), str(target_dir / p.name))
        print("Moved files.")
    else:
        print("Dry-run. Use -a or --apply to move files.")


if __name__ == "__main__":
    main()
