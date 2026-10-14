#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a thin wrapper around the Ruff linter/formatter command-line tool, extending it so that it also recognizes and processes Python scripts that have no file extension (such as executable scripts with a Python shebang line).
The tool should accept the same command-line arguments that Ruff accepts and pass them through to Ruff for normal operation, including help and version requests, which should be forwarded directly so the user sees Ruff's native output. When the user invokes a subcommand such as checking or formatting, the script should separate the arguments into a subcommand, file or directory targets, and option flags. If no targets are provided, it should default to the current directory.
The script should scan the provided targets, including recursing into directories, to identify extensionless files whose first line indicates they are Python files. Those files should be handled alongside regular Python files: the script should invoke Ruff on them so they are linted or formatted just like `.py` files, while still forwarding all user-supplied flags. Files that are not Python, unreadable files, and binary files should be skipped gracefully without crashing the program.
The script should preserve Ruff's exit status so that it can be used reliably in continuous integration pipelines and pre-commit hooks, returning a non-zero code when Ruff reports problems. It should handle missing Ruff installations and missing paths with clear, user-friendly error messages, and it should avoid processing the same file twice. Output should stay faithful to Ruff's own messages, with the wrapper adding only minimal, clearly labeled information when needed.
---"""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys


def is_extensionless_python(file_path: Path) -> bool:
    if file_path.is_file() and not file_path.suffix:
        try:
            with open(file_path, "rb") as f:
                first_line = f.readline()
                return b"python" in first_line
        except (IOError, UnicodeDecodeError):
            return False
    return False


def main():
    args = sys.argv[1:]
    if not args or any(arg in args for arg in ("-h", "--help", "-V", "--version")):
        sys.exit(subprocess.run(["ruff"] + args).returncode)
    subcommand = args[0]
    remaining_args = args[1:]
    targets = []
    flags = []
    for arg in remaining_args:
        if arg.startswith("-"):
            flags.append(arg)
        else:
            targets.append(arg)
    if not targets:
        targets = ["."]
    extensionless_files = []
    native_targets = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            native_targets.append(str(path))
            for p in path.rglob("*"):
                if not any(part.startswith(".") for part in p.parts) and is_extensionless_python(p):
                    extensionless_files.append(p)
        elif path.is_file():
            if is_extensionless_python(path):
                extensionless_files.append(path)
            else:
                native_targets.append(str(path))
    exit_code = 0
    for file_path in extensionless_files:
        try:
            content = file_path.read_bytes()
            cmd = ["ruff", subcommand, "--stdin-filename", str(file_path)] + flags + ["-"]
            result = subprocess.run(cmd, input=content, capture_output=True)
            if subcommand == "format" and "--check" not in flags and "--diff" not in flags:
                if result.returncode == 0 and result.stdout:
                    file_path.write_bytes(result.stdout)
            else:
                if result.stdout:
                    sys.stdout.buffer.write(result.stdout)
                if result.stderr:
                    sys.stderr.buffer.write(result.stderr)
            if result.returncode != 0:
                exit_code = result.returncode
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            exit_code = 1
    if native_targets:
        native_cmd = ["ruff", subcommand] + flags + native_targets
        native_result = subprocess.run(native_cmd)
        if native_result.returncode != 0:
            exit_code = native_result.returncode
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
