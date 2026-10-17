#!/data/data/com.termux/files/usr/bin/python
from pathlib import Path
import re
import sys
import tempfile
from zipfile import ZipFile

from dh import fsz, runcmd
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn


SO_PATTERN = re.compile(r"\.so(\.\d+)*$")
WHL_SUFFIX = ".whl"
console = Console()


def process_file(path: Path) -> None:
    _ret, _, _ = runcmd(["strip", str(path)], show_output=True)


def process_whl(whl_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        with ZipFile(whl_path, "r") as zf:
            zf.extractall(tmpdir_path)
        so_files = [p for p in tmpdir_path.rglob("*") if SO_PATTERN.search(p.name) and p.is_file()]
        for so_file in so_files:
            process_file(so_file)
        with ZipFile(whl_path, "w") as zf:
            for path in tmpdir_path.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(tmpdir_path))


def collect_files(cwd: Path, args: list[str]) -> list[Path]:
    if args:
        return [Path(p) for p in args]
    so_files = [p for p in cwd.rglob("*") if SO_PATTERN.search(p.name) and p.is_file()]
    whl_files = [p for p in cwd.rglob("*") if p.is_file() and p.suffix == WHL_SUFFIX]
    return so_files + whl_files


def show_summary(files: list[Path]) -> None:
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    console.print(f"[bold cyan]Total number of files:[/] [bold yellow]{len(files)}[/]")
    console.print(f"[bold cyan]Total size of files:[/] [bold yellow]{fsz(total_size)}[/]")


def process_whl_files(whl_files: list[Path]) -> None:
    for whl_file in whl_files:
        console.print(f"[bold blue]Processing wheel:[/] [bold yellow]{whl_file}[/]")
        process_whl(whl_file)


if __name__ == "__main__":
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = collect_files(cwd, args)
    so_files = [f for f in files if SO_PATTERN.search(f.name) and f.is_file() and f.suffix != WHL_SUFFIX]
    whl_files = [f for f in files if f.is_file() and f.suffix == WHL_SUFFIX]

    console.print("[bold green]Starting .so stripping process...[/]")
    show_summary(so_files + whl_files)

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

    console.print(
        f"[bold green]Done![/] Processed [bold yellow]{len(so_files)}[/] .so files "
        f"and [bold yellow]{len(whl_files)}[/] .whl archives."
    )
    show_summary(so_files + whl_files)
