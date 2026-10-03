#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line utility that strips debug symbols from shared object (.so) files using the "strip" command, and additionally supports processing .whl (wheel) archives by extracting them, stripping any .so files found inside (matching patterns like .so, .so.1, etc.), and repackaging them back into a zip.
It should accept file paths as arguments, or if none are given, recursively discover .so files in the current working directory.
The script must use the "rich" library to display a formatted summary showing the total count and total size (via a fsz helper) of the files processed, along with a progress bar during processing, and it should run external "strip" commands via a runcmd helper, showing their output."""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

from dh import fsz, runcmd
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn

SO_PATTERN = re.compile(r"\.so(\.\d+)*$")
console = Console()


def process_file(path: Path) -> None:
    _ret, _, _ = runcmd(["strip", str(path)], show_output=True)


def process_whl(whl_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        with ZipFile(whl_path, "r") as zf:
            zf.extractall(tmpdir)
        so_files = [p for p in tmpdir.rglob("*") if SO_PATTERN.search(p.name)]
        for so_file in so_files:
            process_file(so_file)
        with ZipFile(whl_path, "w") as zf:
            for path in tmpdir.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(tmpdir))


def collect_files(cwd: Path, args: list[str]) -> list[Path]:
    if args:
        return [Path(p) for p in args]
    so_files = [p for p in cwd.rglob("*") if SO_PATTERN.search(p.name) and p.is_file()]
    return so_files


def show_summary(files: list[Path]) -> None:
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    console.print(f"[bold cyan]Total number of .so files:[/] [bold yellow]{len(files)}[/]")
    console.print(f"[bold cyan]Total size of .so files:[/] [bold yellow]{fsz(total_size)}[/]")


if __name__ == "__main__":
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = collect_files(cwd, args)
    so_files = [f for f in files if f.suffix == ".so" or SO_PATTERN.search(f.name)]
    console.print("[bold green]Starting .so stripping process...[/]")
    show_summary(so_files)
    with Progress(
        TextColumn("[bold blue]{task.description}[/]"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[bold]{task.completed}/{task.total}[/]"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Stripping .so files...[/]", total=len(so_files))
        for so_file in so_files:
            process_file(so_file)
            progress.update(task, advance=1)
    console.print(f"[bold green]Done![/] Processed [bold yellow]{len(so_files)}[/] .so files.")
    show_summary(so_files)
