#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
from collections import deque
from multiprocessing import Lock, Pool
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any
from dh import runcmd

if TYPE_CHECKING:
    from collections.abc import Iterator
MAX_WORKERS = 8
print_lock = Lock()


def walk_files(directory: Path) -> Iterator[Path]:
    for root, _dirs, files in directory.walk():
        for name in files:
            yield root / name


def is_python_file(path: Path) -> bool:
    if path.suffix == ".py":
        return True
    if path.suffix == "":
        try:
            with path.open("rb") as f:
                head = f.read(64)
                if b"python" in head and b"#!" in head:
                    return True
        except Exception:
            return False
    return False


def process_file(path: Path) -> None:
    path = Path(path)
    print(f"[OK] {path.name}")
    cmd = [
        "ruff",
        "check",
        "--fix",
        "--unsafe-fixes",
        "--line-length",
        "120",
        "--quiet",
        str(path),
    ]
    rc_check, out_check, err_check = runcmd(cmd, show_output=True)
    format_cmd = [
        "ruff",
        "format",
        "--config",
        "/data/data/com.termux/files/home/.config/ruff/ruff.toml",
        str(path),
    ]
    rc_fmt, _out_fmt, err_fmt = runcmd(format_cmd, show_output=True)
    output: list[str] = []
    if rc_check != 0 or err_check.strip():
        output.append(f"--- Issues fixing {path.name} ---")
        if err_check.strip():
            output.append(err_check.strip())
        if out_check.strip():
            output.append(out_check.strip())
    if rc_fmt != 0 or err_fmt.strip():
        output.append(f"--- Issues formatting {path.name} ---")
        if err_fmt.strip():
            output.append(err_fmt.strip())
    if output:
        with print_lock:
            print("\n".join(output))
            sys.stdout.flush()


def get_all_files(cwd: Path) -> list[Path]:
    py_files: list[Path] = []
    for path in walk_files(cwd):
        if path.is_file() and is_python_file(path):
            py_files.append(path)
    return py_files


def main() -> None:
    cwd = Path.cwd()
    files = get_all_files(cwd)
    if not files:
        print("no file found.")
        return
    pool = Pool(processes=MAX_WORKERS)
    pending: deque[Any] = deque()
    for f in files:
        pending.append(pool.apply_async(process_file, (f,)))
        if len(pending) > 32:
            pending.popleft().get()
    while pending:
        pending.popleft().get()
    pool.close()
    pool.join()


if __name__ == "__main__":
    raise SystemExit(main())
