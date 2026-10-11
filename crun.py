#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to recreate a Python script with the following specification. Do not include code. Output only the prompt.

---

Create a single Python 3 script intended to run under Termux on Android (shebang pointing to the Termux Python at /data/data/com.termux/files/usr/bin/env python). The script walks a directory tree, finds C and C++ source files, and compiles each one with clang or clang++. It is a compile-everything utility meant to be run from the current working directory.

**Module setup**
- Begin with the Termux shebang line.
- Enable postponed evaluation of annotations (`from __future__ import annotations`) so type hints like `str | Path` are valid.
- Use `pathlib.Path` for all filesystem paths.

**Dependencies**
- Standard library: `pathlib`, `os` (use `os.walk`), `typing` as needed.
- Third-party/local helper module named `dh` (not standard library) that must be imported as: `fsz`, `gsz`, `mpf`, `should_skip`. Assume these exist. Their roles are:
  - `should_skip(path)`: returns True for paths that should be excluded from traversal and processing (e.g., ignored directories or files). Used both to prune directories and to filter files.
  - `gsz(path)`: returns a size measurement for a directory (used to record the starting size of the working directory).
  - `fsz`: a size formatting/conversion helper for human-readable sizes.
  - `mpf`: a helper for formatting or printing results (e.g., a message/progress or formatted output). Import it even if used lightly.
  - `run_command` is referenced by the processing logic but is NOT among the imports shown; the agent must make it available. Implement it locally as a helper that runs a shell command via `subprocess` (capturing stdout and stderr as text, returning a tuple of return code, stdout text, and stderr text). Handle the case where the command cannot be launched gracefully.

**Function: get_filez(root_dir)**
- Generator function. Accepts a string or Path.
- Converts root to a Path.
- If root is a directory: walk it top-down with `os.walk`. Maintain a set of visited resolved directory paths to avoid revisiting (e.g., symlink loops). For each subdirectory in the current listing (iterate over a copy so removal is safe): compute its full path and resolved path; remove it from the walk list if `should_skip` is True or its resolved path was already visited; add the resolved path to the visited set. For each file in the current directory not skipped by `should_skip`, yield its Path.
- If root is not a directory (a single file or nonexistent path): yield the root path itself without checking existence further.
- Note the intended behavior: pruning should be applied to subdirectories before descent; visited tracking should prevent duplicate traversal.

**Function: process_file(path)**
- Convert input to a Path. If it does not exist, return False.
- If the suffix is `.c`, build a command that invokes `clang` with the source file and outputs an executable with the suffix removed (use the path's stem-without-suffix, i.e., the same path with suffix stripped).
- If the suffix is `.cpp`, build the same kind of command using `clang++`.
- Execute the command via `run_command`, print the captured text output, and return the return code.
- Edge case to handle deliberately: for suffixes other than `.c` or `.cpp`, no command is defined; the reference behavior leaves `cmd` unset and would raise. The rewritten script should instead return a non-zero/False result cleanly without crashing (and should not attempt compilation). Also use `elif`/explicit checks rather than sequential ifs so the two branches are mutually clear.

**Function: main()**
- Get the current working directory via `Path.cwd()`.
- Record the starting size of the directory using `gsz(cwd)`.
- Collect files by iterating `get_filez(cwd)` and keeping only entries where `path.is_file()` is true (the reference script is truncated at this point; complete the loop by appending matching paths to a list).
- Then, for each collected file, call `process_file`, which compiles C and C++ sources. Count successes and failures.
- After processing, compute the ending size of the directory with `gsz(cwd)` and report the difference (using `fsz` for human-readable output and `mpf` for formatted messaging), so the user sees how much the build artifacts changed disk usage.
- Print a concise summary: number of files attempted, succeeded, failed, and size change.

**Entry point**
- Guard the execution with `if __name__ == "__main__":` and call `main()`.

**Error handling and robustness**
- Do not crash on missing files, unsupported suffixes, or command failures; report them and continue.
- Do not follow symlink loops during traversal.
- Handle `run_command` launch failures (e.g., clang not installed) by returning a nonzero code and an error message rather than raising an unhandled exception.
- Ensure failed compilations are counted but do not stop the overall run.

**Usage**
- Run from the directory containing the sources: `python <scriptname>.py`. The script recursively compiles all `.c` and `.cpp` files under the current directory, placing each executable next to its source with the extension removed.
- Requires `clang` and `clang++` available on PATH in Termux.

**Output**
- Print each command's captured output as it runs, followed by the final summary.
- Use type hints for function signatures (`-> None` for `main`, and appropriate return types for others).

Keep the implementation idiomatic, concise, and with comments only where logic is non-obvious.
---"""

from __future__ import annotations

from pathlib import Path

from dh import fsz, gsz, mpf, should_skip


def get_filez(root_dir: str | Path):
    from os import walk as os_walk

    visited_dirs: set[Path] = set()
    root_dir = Path(root_dir)
    if root_dir.is_dir():
        for dirpath, dirnames, filenames in os_walk(root_dir, topdown=True):
            base_path = Path(dirpath)
            for dirname in list(dirnames):
                full_path = base_path / dirname
                resolved_path = full_path.resolve()
                if should_skip(full_path) or resolved_path in visited_dirs:
                    dirnames.remove(dirname)
                visited_dirs.add(resolved_path)
            for filename in filenames:
                path = Path(dirpath) / filename
                if not should_skip(path):
                    yield path
    else:
        yield root_dir


def process_file(path):
    path = Path(path)
    if not path.exists():
        return False
    if path.suffix == ".c":
        cmd = f"clang {path!s} -o {path.with_suffix('')!s}"
    if path.suffix == ".cpp":
        cmd = f"clang++ {path!s} -o {path.with_suffix('')!s}"
    ret, txt, _err = run_command(cmd)
    print(txt)
    return ret


def main() -> None:
    cwd = Path().cwd()
    start_size = gsz(cwd)
    files = []
    for path in get_filez(cwd):
        if path.is_file() and path.suffix in {".c", ".cpp"}:
            files.append(path)
    mpf(process_file, files)
    print(f"{fsz(start_size - gsz(cwd))}")


if __name__ == "__main__":
    raise SystemExit(main())
