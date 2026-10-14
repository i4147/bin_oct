#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that checks the syntax of C and C++ source files using the system's Clang compilers. The tool should accept an optional list of file paths from the command line; if none are given, it should automatically discover all C and C++ source and header files (including common extensions such as .c, .h, .inc, .cpp, .cc, .cxx, .hpp, .hh, .hxx, and .hpp11) under the current working directory. For C-family files, use the C syntax-only check; for C++ files, use the C++ syntax-only check, without generating any object or output files.
The script should run these checks concurrently using a bounded pool of worker processes (around eight workers), keeping a limited number of tasks in flight at once so that memory use stays controlled on large projects. Each file's result should capture the file path, the compiler's exit code, and its standard output and error text.
After all checks complete, the script should report the results clearly to the user: list each file that failed with its diagnostic output, and provide a summary showing how many files passed and how many failed. The script should exit with a non-zero status if any file fails validation and zero if all pass. Handle missing compiler binaries or unreadable files gracefully with informative messages rather than crashing.
---"""

from __future__ import annotations
from collections import deque
from multiprocessing import get_context
from pathlib import Path
import sys
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
