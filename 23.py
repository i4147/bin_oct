#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively scans a given directory (using a fast file-walking utility) to find Python files, including extensionless files whose shebang line references "python", then lints and auto-fixes them in parallel using "ruff check --fix --unsafe-fixes" (with a 120-character line length) followed by "ruff format" with a specified config file.
It should run these operations concurrently across multiple files using a process pool (up to 8 workers), print a status line for each processed file, and collect/print any error output or issues encountered during the check or format steps under clearly labeled sections for each file.
The script takes a target directory (or files) as input via command-line arguments and produces console output summarizing successes and problems, using a lock to keep printed output from interleaving across worker processes."""

import sys
from multiprocessing import Lock, Pool
from pathlib import Path
from dh import runcmd
from fastwalk import walk_files

MAX_WORKERS = 8
print_lock = Lock()


def is_python_file(path: Path) -> bool:
    if path.suffix == ".py":
        return True
    if path.suffix == "":
        try:
            with Path(path).open("rb") as f:
                head = f.read(64)
                if b"python" in head and b"#!" in head:
                    return True
        except Exception:
            return False
    return False


def process_file(path: str | Path) -> None:
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
    output = []
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


def get_all_files(cwd: Path):
    py_files = []
    for pth in walk_files(cwd):
        path = Path(pth)
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
    pending = deque()
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
