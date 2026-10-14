#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line tool for compiling and immediately running a single C or C++ source file. The tool should accept a source file path as its first argument, along with any additional arguments that should be forwarded to the compiled program. It should display a usage message when invoked without arguments.
Before compiling, the tool should validate the input: confirm the file exists, expand user paths and resolve relative paths, and reject files whose extension is not a supported C or C++ type (such as .c, .cpp, .cc, or .cxx). For each supported extension, prefer a modern compiler (clang-based for C and C++) but automatically fall back to an alternative compiler (such as gcc or g++) if the preferred one is not installed. If no suitable compiler is available, report a clear error message to the user and exit with a non-zero status.
Compile the source file into a temporary or cached executable, using sensible default flags for a standard, readable build. If compilation fails, display the compiler's error output and stop without running anything. If compilation succeeds, make the resulting binary executable if needed, run it with the forwarded arguments, stream its standard input, output, and error to the terminal, and return the program's exit code as the tool's own exit code. Errors and diagnostic messages should go to standard error, while normal program output should appear on standard output. The tool should handle missing files, unsupported types, missing compilers, and compilation failures gracefully with informative messages rather than unhandled exceptions.
---"""

from __future__ import annotations
import os
from pathlib import Path
import stat
import sys
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
