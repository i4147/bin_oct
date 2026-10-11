#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script which recursively finds all `.py` files under a given directory, runs a selected set of static type checkers and linters on each file in parallel, and appends each file's combined tool output to a file. Specify the following:

**Purpose:** A batch type-checking and linting runner for Python projects, designed for Termux (Android) environments, that collects output from multiple checkers per file and writes results into a report file.

**Interface:** Use argparse. Accept a root directory argument (a path to scan recursively) and a way to select which tools to run from a fixed set of five: ty, pyright, pylint, pyrefly, and mypy. Tool selection should allow choosing one or more tools, with an option to run all. The script should use a shebang line pointing to the Termux Python interpreter path and include `from __future__ import annotations`.

**Tool invocation rules:**
- ty: run `ty check <file>`
- pyright: run `pyright <file>`
- pylint: run `pylint -E <file>` (errors only)
- pyrefly: run `pyrefly check <file>`
- mypy: run `mypy <file>`
- Any unrecognized tool name returns no output (nothing is reported for it).

**Execution helper:** A function runs a command via subprocess with captured stdout and stderr as text, without raising on nonzero exit codes. It returns the exit code and the concatenation of stdout followed by stderr. Exit codes from tools are ignored for reporting purposes; only the output matters.

**Per-file tool runner:** For a given tool and file path, build the command, run it, and return the tool name paired with its output, or `None` if the output is empty or whitespace-only. Handle errors: if the executable is not found, return an error string of the form "ERROR: <tool> not found in PATH"; for any other exception, return "ERROR: " followed by the exception message.

**Output writing:** For each file, append to a results file (opened in append mode with UTF-8 encoding) a leading blank-line separator, then for each tool write its section. Include the file header, the tool name, and the output (skipping tools whose output is `None`). Write with clear section delimiters so each file's results are readable.

**Parallelism:** Use `multiprocessing.Pool` to process files concurrently, distributing per-file (or per-file-and-tool) work across worker processes. Collect results and write them in a deterministic order where practical. Make sure the pool is properly closed and joined, and that the main logic is guarded by `if __name__ == "__main__":`.

**File discovery:** Use `Path.rglob("*.py")` via a generator function, so discovery is recursive and lazy. Consider and handle the case where the root path does not exist or is not a directory, printing a clear error and exiting with a nonzero status.

**Edge cases to address:**
- Empty directories or no `.py` files: exit cleanly with a message.
- Tools not installed: the error string is recorded in the output rather than crashing.
- Files with non-UTF-8 content or unusual names: handle gracefully.
- Tool output containing only whitespace is treated as no output.
- Ensure the results file is created or appended correctly, and mention in the script where it is written.

**Dependencies:** Only the Python standard library (argparse, subprocess, multiprocessing, pathlib). The external checkers (ty, pyright, pylint, pyrefly, mypy) must be available on PATH at runtime.

**Usage:** Run as an executable script from the command line with the directory and tool selection as arguments. Print a brief progress or completion message to the console, such as the number of files processed and the output file location.

Keep the code idiomatic, with type hints using modern syntax, concise docstrings or comments where they aid understanding, and consistent naming.
---"""

from __future__ import annotations

import argparse
import subprocess
from multiprocessing import Pool
from pathlib import Path


def get_pyfiles_iter(root: Path):
    yield from root.rglob("*.py")


def runcmd(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    return proc.returncode, combined


def run_tool(tool: str, path: Path) -> tuple[str, str | None]:
    try:
        if tool == "ty":
            cmd = ["ty", "check", str(path)]
        elif tool == "pyright":
            cmd = ["pyright", str(path)]
        elif tool == "pylint":
            cmd = ["pylint", "-E", str(path)]
        elif tool == "pyrefly":
            cmd = ["pyrefly", "check", str(path)]
        elif tool == "mypy":
            cmd = ["mypy", str(path)]
        else:
            return tool, None
        _returncode, output = runcmd(cmd)
        return tool, output if output.strip() else None
    except FileNotFoundError:
        return tool, f"ERROR: {tool} not found in PATH"
    except Exception as e:
        return tool, f"ERROR: {e!s}"


def append_tool_outputs(path: Path, outputs: dict[str, str | None]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write("\n\n")
        for tool, output in outputs.items():
            f.write(f"# ===== {tool} output =====\n")
            if output:
                for line in output.split("\n"):
                    if line.strip():
                        f.write(f"# {line}\n")
            else:
                f.write("# (no issues)\n")


def process_file(path: Path, tools: list[str]) -> str:
    outputs = {}
    for tool in tools:
        tool_name, output = run_tool(tool, path)
        outputs[tool_name] = output
    if (tools == ["ty"] and outputs.get("ty") and ("all checks passed" in outputs["ty"].lower())) or (
        "error[unresolved-import]: Cannot resolve imported module `dh`" in outputs["ty"].lower()
    ):
        return f"✓ Skipped (ty: all checks passed): {path}"
    append_tool_outputs(path, outputs)
    return f"✓ Updated: {path}"


def collect_pyfiles(paths: list[str]):
    for path_str in paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            yield from get_pyfiles_iter(path)


def main():
    parser = argparse.ArgumentParser(
        description="Run code checkers and append outputs to Python files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python script.py file.py
  python script.py . -a
  python script.py . -g -p
  python script.py dir/ -r
  python script.py file1.py file2.py -g -p
        """,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Python files or directories to process (default: . recursively)",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Run all tools: ty, pyright, pylint, pyrefly",
    )
    parser.add_argument(
        "-g",
        "--pyright",
        action="store_true",
        help="Run pyright",
    )
    parser.add_argument(
        "-p",
        "--pylint",
        action="store_true",
        help="Run pylint",
    )
    parser.add_argument(
        "-r",
        "--pyrefly",
        action="store_true",
        help="Run pyrefly",
    )
    parser.add_argument(
        "-t",
        "--ty",
        action="store_true",
        help="Run ty",
    )
    parser.add_argument(
        "-m",
        "--mypy",
        action="store_true",
        help="Run mypy",
    )
    args = parser.parse_args()
    paths = args.paths or ["."]
    enabled_tools = []
    if args.all:
        enabled_tools = ["ty", "pyright", "pylint", "pyrefly", "mypy"]
    else:
        if args.ty:
            enabled_tools.append("ty")
        if args.pyright:
            enabled_tools.append("pyright")
        if args.pylint:
            enabled_tools.append("pylint")
        if args.pyrefly:
            enabled_tools.append("pyrefly")
        if args.mypy:
            enabled_tools.append("mypy")
        if not enabled_tools:
            enabled_tools = ["ty", "pyright", "pyrefly"]
    files = list(collect_pyfiles(paths))
    if not files:
        print("No .py files found.")
        return
    with Pool(processes=4) as pool:
        async_results = [pool.apply_async(process_file, args=(f, enabled_tools)) for f in files]
        for result in async_results:
            print(result.get())


if __name__ == "__main__":
    raise SystemExit(main())
