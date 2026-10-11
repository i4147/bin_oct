#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that asks an a Termux-targeted Specify the purpose, inputs and outputs, compiler selection and fallback order, extension-to-compiler mapping, temp directory handling, standard flags, error messages with exit codes, and the dependency on the `sh` library. Include the execution entry point and usage behavior.

Build a Python command-line script for the Termux environment on Android that compiles a single C or C++ source fileediately runs the resulting executable, forwarding any extra command-line arguments to the program.

**Target environment and shebang:** Use the Termux Python interpreter path `/data/data/com.termux/files/usr/bin/env python` as the shebang line. Begin the file with `from __future__ import annotations`.

**Dependencies:** Use only the standard library modules `os`, `stat`, `sys`, and `pathlib.Path`, plus the third-party `sh` package, used for locating executables (`sh.which`) and for running the compiled program and compiler commands. Use `sh` for command execution rather than `subprocess`.

**Supported source types and compiler mapping:** Define a module-level dictionary mapping lowercase file extensions to a tuple of (preferred compiler, tuple of fallback compilers):
- `.c` → preferred `clang`, fallbacks `clang`, `gcc`
- `.cpp`, `.cc`, `.cxx` → preferred `clang++`, fallbacks `clang++`, `g++`

**Helper function:** Implement `_pick_compiler(candidates)` that iterates the candidate names in order and returns the first one for which `sh.which` finds an executable, or `None` if none are found.

**Main function:** Implement `cpp_run(*args)` that returns an integer exit status:
1. If no arguments are given, print a usage line of the form `Usage: cpprun <file.c|file.cpp|file.cc> [args...]` to standard output and return 1.
2. Take the first argument as the source path, expand `~`, and resolve it to an absolute path. If it is not an existing regular file, print an error to standard error naming the resolved path as not found and return 1.
3. Determine the extension via lowercase suffix. If it is not in the mapping, print an error to standard error listing the unsupported extension and the expected extensions (comma-separated), and return 1.
4. Select the compiler with `_pick_compiler` over the preferred name followed by its fallbacks. If none is found, print to standard error: `Error: no compiler found. Run: pkg install clang` and return 1.
5. Determine a temporary build directory: use the `TMPDIR` environment variable if set and non-empty; otherwise use `$PREFIX/tmp`, where `PREFIX` defaults to `/data/data/com.termux/files/usr`. Create it with parents and tolerate it already existing.
6. Set the output executable path to the temp directory joined with the source file's stem (name without extension).
7. Choose the C standard flag: `-std=c17` for `.c` files; for C++ files use a C++ standard flag (such as `-std=c++17`). Build and compile the source into the executable using the chosen compiler, with the standard flag and the source file as inputs, and capture or let errors propagate so compilation failures produce a non-zero result and a clear message.
8. Make the output executable with appropriate permission bits (owner/group/other execute, preserving existing mode bits using `stat` constants).
9. Run the compiled executable with the remaining command-line arguments (everything after the source path), forwarding its standard output and error, and return its exit code.

**Entry point:** When run as the main program, call `cpp_run` with the command-line arguments excluding the script name, and exit the process with the returned status via `sys.exit`.

**Error handling and edge cases:** Handle a missing file, unsupported extension, missing compiler, and compilation failure (returning a non-zero status and reporting the failure). Handle `~` in the path, mixed-case extensions, and a missing or empty `TMPDIR`. Ensure that arguments after the source file are passed through unchanged, including ones that start with dashes. Keep the temp directory creation idempotent.

**Style:** Use concise functions, type-neutral plain Python, no classes, and clear short error messages written to standard error where indicated.
---"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import sh

COMPILERS = {
    ".c": ("clang", ("clang", "gcc")),
    ".cpp": ("clang++", ("clang++", "g++")),
    ".cc": ("clang++", ("clang++", "g++")),
    ".cxx": ("clang++", ("clang++", "g++")),
}


def _pick_compiler(candidates):
    for c in candidates:
        if sh.which(c):
            return c
    return None


def cpp_run(*args):
    if not args:
        print("Usage: cpprun <file.c|file.cpp|file.cc> [args...]")
        return 1
    src = Path(args[0]).expanduser().resolve()
    if not src.is_file():
        print(f"Error: {src} not found", file=sys.stderr)
        return 1
    ext = src.suffix.lower()
    if ext not in COMPILERS:
        print(
            f"Error: unsupported extension '{ext}'. Expected one of: {', '.join(COMPILERS)}",
            file=sys.stderr,
        )
        return 1
    preferred, fallbacks = COMPILERS[ext]
    compiler_name = _pick_compiler((preferred, *fallbacks))
    if compiler_name is None:
        print("Error: no compiler found. Run: pkg install clang", file=sys.stderr)
        return 1
    tmpdir = Path(os.environ.get("TMPDIR") or f"{os.environ.get('PREFIX', '/data/data/com.termux/files/usr')}/tmp")
    tmpdir.mkdir(parents=True, exist_ok=True)
    exe = tmpdir / src.stem
    std_flag = "-std=c17" if ext == ".c" else "-std=c++17"
    compiler = sh.Command(compiler_name)
    try:
        compiler(
            std_flag,
            "-Wall",
            "-Wextra",
            "-O2",
            str(src),
            "-o",
            str(exe),
            _out=sys.stdout,
            _err=sys.stderr,
        )
    except sh.ErrorReturnCode as e:
        return e.exit_code
    except sh.CommandNotFound:
        print(f"Error: {compiler_name} not found on PATH", file=sys.stderr)
        return 1
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    try:
        prog = sh.Command(str(exe))
        prog(
            *args[1:],
            _in=sys.stdin,
            _out=sys.stdout,
            _err=sys.stderr,
        )
    except sh.ErrorReturnCode as e:
        return e.exit_code
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(cpp_run(*sys.argv[1:]))
