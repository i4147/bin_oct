#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that compiles Python source files into bytecode in parallel and reports how the a result.
The tool should run from the current working directory. If the user supplies one or more file paths on the command line, compile only those files. If no paths are given, discover all Python source files beneath the current directory automatically. Skip any file that does not exist, and ignore anything located inside version-control metadata directories.
Compilation should be done with the standard, non-legacy bytecode layout at the default optimization level, so that the resulting cache artifacts match what the interpreter would normally produce. Processing should be parallelized across a small pool of worker processes, using a spawn-based start method so it behaves consistently across platforms. Limit how many jobs are queued at once so memory use stays bounded even when there are thousands of files, and make sure every submitted job is awaited before the script finishes.
Before any work begins, measure the total size of the current directory tree. After all compilation completes, measure it again. Report the before size, the after size, and the difference, clearly stating whether the directory grew or shrank (using a plus or minus indication), and present sizes in human-readable units such as bytes, KB, MB, or GB.
The script should exit cleanly on success, and any errors raised by individual workers should propagate so the user is aware of failures. Keep the output concise and suitable for a command-line terminal.
---"""

from __future__ import annotations
from collections import deque
import compileall
from multiprocessing import get_context
from pathlib import Path
import sys
from dh import fsz, get_files, gsz

MAX_QUEUE = 4


def process_file(path) -> bool | None:
    path = Path(path)
    if not path.exists():
        return False
    if ".git" in path.parts:
        return None
    compileall.compile_file(path, legacy=False, optimize=0)
    return True


def main() -> None:
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    files = [Path(f) for f in args] if args else get_files(cwd, ext=[".py"])
    with get_context("spawn").Pool(8) as pool:
        pending = deque()
        for f in files:
            pending.append(pool.apply_async(process_file, (f,)))
            if len(pending) > MAX_QUEUE:
                pending.popleft().get()
        while pending:
            pending.popleft().get()
    after = gsz(cwd)
    diff_size = before - after
    if after > before:
        sign = "+"
    elif before > after:
        sign = "-"
    print(f"space changed : {sign} {fsz(diff_size)}")


if __name__ == "__main__":
    raise SystemExit(main())
