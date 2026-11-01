#!/data/data/com.termux/files/usr/bin/env python

"""23.py -- format every Python file under the working directory with ``ruff``.

Each file is passed to ``ruff check --fix --unsafe-fixes`` and then to
``ruff format``, so imports and other safe rewrites are applied before the
formatter runs.  Files are handled by a small process pool (``MAX_WORKERS``)
and diagnostics are printed per file, prefixed with the reason they were
reported.

The file is considered Python when it ends in ``.py`` or when it has no
suffix but starts with a ``#!`` line naming Python.
"""

from __future__ import annotations

import sys
from collections import deque
from multiprocessing import Lock, Pool
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dh import runcmd

if TYPE_CHECKING:
    from collections.abc import Iterator
MAX_WORKERS = 8
print_lock = Lock()


def walk_files(directory: Path) -> Iterator[Path]:
    """Yield every file below *directory*, recursively."""
    for root, _dirs, files in directory.walk():
        for name in files:
            yield root / name


def is_python_file(path: Path) -> bool:
    """Return ``True`` when *path* holds Python source.

    A file counts as Python when its suffix is ``.py``, or when it has no suffix
    and the first 64 bytes are a shebang line naming Python.  Files that cannot
    be opened are treated as non-Python.
    """
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
    """Run ``ruff check --fix`` and then ``ruff format`` on one file.

    Diagnostics produced by either command are printed together under a header
    naming the file; the shared ``print_lock`` keeps the output of concurrent
    workers from interleaving.
    """
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
    """Return every Python file below *cwd*, following symlinks."""
    py_files: list[Path] = []
    for path in walk_files(cwd):
        if path.is_file() and is_python_file(path):
            py_files.append(path)
    return py_files


def main() -> None:
    """Collect the Python files below the working directory and process them.

    At most 32 jobs are kept in flight; the rest are dispatched as earlier ones
    complete.
    """
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
