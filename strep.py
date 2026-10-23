#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
from pathlib import Path
import re
import sys
import tempfile
from zipfile import ZipFile
from dh import fsz, runcmd
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from dh import get_size
SO_RE = re.compile(r"\.so(\.\d+)*$", re.IGNORECASE)
WHL_SUFFIX = ".whl"
console = Console()
def process_file(path: Path) -> None:
    _ret, _, _ = runcmd(["strip", str(path)], show_output=True)
def process_whl(whl_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        with ZipFile(whl_path, "r") as zf:
            zf.extractall(tmpdir_path)
        so_files = [p for p in tmpdir_path.rglob("*") if SO_RE.search(p.name) and p.is_file()]
        for so_file in so_files:
            process_file(so_file)
        with ZipFile(whl_path, "w") as zf:
            for path in tmpdir_path.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(tmpdir_path))
def collect_files(cwd: Path, args: list[str]) -> list[Path]:
    if args:
        return [Path(p) for p in args]
    so_files = [p for p in cwd.rglob("*") if SO_RE.search(p.name) and p.is_file()]
    whl_files = [p for p in cwd.rglob("*") if p.is_file() and p.suffix == WHL_SUFFIX]
    return so_files + whl_files
def show_summary(files: list[Path]) -> int:
    return sum(f.stat().st_size for f in files if f.is_file())
def process_whl_files(whl_files: list[Path]) -> None:
    for whl_file in whl_files:
        console.print(f"[bold blue]Processing wheel:[/] [bold yellow]{whl_file}[/]")
        process_whl(whl_file)
def has_so(path: str | Path) -> bool:
    path = Path(path)
    with ZipFile(path, "r") as zf:
        return any(SO_RE.search(name) for name in zf.namelist())
if __name__ == "__main__":
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = collect_files(cwd, args)
    so_files = [f for f in files if SO_RE.search(f.name) and f.is_file() and f.suffix != WHL_SUFFIX]
    whl_files = [f for f in files if f.is_file() and f.suffix == WHL_SUFFIX and has_so(f)]
    files_to_process = so_files + whl_files
    before = get_size(files_to_process)
    with Progress(
        TextColumn("[bold blue]{task.description}[/]"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[bold]{task.completed}/{task.total}[/]"),
        console=console,
    ) as progress:
        task = progress.add_task(
            "[cyan]Stripping .so files...[/]",
            total=len(so_files) + len(whl_files),
        )
        for so_file in so_files:
            process_file(so_file)
            progress.update(task, advance=1)
        for whl_file in whl_files:
            process_whl(whl_file)
            progress.update(task, advance=1)
    after = get_size(files_to_process)
    space_freed = before - after
    console.print(f"[bold cyan]Num:[/] [bold yellow]{len(files_to_process)}[/]")
    console.print(f"[bold cyan]Size:[/] [bold yellow]{fsz(space_freed)}[/]")
