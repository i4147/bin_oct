#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line script that validates C/C++ source files for syntax errors using clang and clang++.
It should accept file paths as command-line arguments, or if none are given, recursively discover files with common C/C++ extensions (.c, .cc, .cpp, .cxx, .h, .hh, .hpp, .hxx, .inc, hpp11) in the current working directory via a helper `get_files` function.
For each file, run `clang -fsyntax-only` (for C files) or `clang++ -fsyntax-only` (for C++ files) in parallel using a multiprocessing Pool (spawn context, 8 workers) with a bounded pending-task queue, collecting the return code, stdout, and stderr for each.
Finally, iterate over the results and print a colored error message (using a `cprint` helper) for each file whose validation return code equals 2, indicating a syntax error."""

import sys
from collections import deque
from multiprocessing import get_context
from pathlib import Path
from dh import cprint, get_files

c_files = {".c", ".h", ".inc"}
cpp_files = {".cpp", ".cc", ".cxx", ".hpp", ".hpp11", ".hh", ".hxx"}


def validate_cpp(path: Path) -> tuple[bool, str]:
    cmd = ""
    if path.suffix in c_files:
        cmd = "clang -fsyntax-only str(path)"
    if path.suffix in cpp_files:
        cmd = "clang++ -fsyntax-only str(path)"
    ret, txt, err = run_command(cmd)
    return (path, ret, txt, err)


if __name__ == "__main__":
    args = sys.argv[1:]
    cwd = Path.cwd()
    files = (
        [Path(p) for p in args]
        if args
        else get_files(
            cwd,
            ext=[
                ".c",
                ".cc",
                ".cpp",
                ".cxx",
                ".h",
                ".hh",
                ".hpp",
                ".hxx",
                ".inc",
                "hpp11",
            ],
        )
    )
    results = []
    with get_context("spawn").Pool(8) as pool:
        pending = deque()
        for f in files:
            pending.append(pool.apply_async(validate_cpp, (f,)))
            if len(pending) > 8:
                results.append(pending.popleft().get())
        while pending:
            results.append(pending.popleft().get())
    for result in results:
        if int(result[1]) == 2:
            cprint(f"[✖] : {result[0].name} has error", "white")
        else:
            cprint(f"[✅] : {result[0].name} is ok", "cyan")
