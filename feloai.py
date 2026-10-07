#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python 3.12 script (intended to run under Termux on Android, using the Termux usr/bin/python3.12 interpreter) that acts as a thin command-line wrapper/launcher for a Node.js-based "felo" search/agent tool.

Purpose:
- The script should accept a search query as command-line arguments (joined into a single string), forward it to a Node.js script located at a fixed path (e.g. "/data/data/com.termux/files/home/bashbin/felo-sa.mjs") by invoking it with `node <script_path> --query <query>`, stream/display its output live to the console, and simultaneously log the full session (start time, working directory, arguments, captured output, end time, and exit code) to a timestamped log file.

Main inputs:
- Command-line arguments passed to the script represent the user's query (e.g. `felo <query>`). If no arguments are provided, print a usage message ("Usage: felo <query>") to stderr and exit with status code 2.

Main outputs:
- Real-time output from the underlying Node.js subprocess shown to the user on stdout/stderr as it runs.
- A persistent log file written under `~/tmp/apps`, named like `felo_<YYYYMMDD_HHMMSS_microseconds>.txt`, with automatic collision-avoidance by appending an incrementing counter suffix if a file with that timestamp already exists.
- Each log file should contain a header section (a separator line, "Started" timestamp, current working directory, and the raw argument list), followed by the captured output, then a footer section (a separator line, "End" marker, "Finished" timestamp, and the subprocess exit code).
- The script's own exit code should reflect the exit code of the underlying Node.js subprocess (or the usage-error code 2 if no query was given).

Notable behavior/requirements:
- Use `datetime`, `pathlib.Path`, `subprocess`, `os`, and `sys` modules.
- Ensure the log directory is created (including parent directories) if it doesn't exist, using `Path.home() / "tmp" / "apps"`.
- Timestamps in filenames should use microsecond precision (`%Y%m%d_%H%M%S_%f`) and timestamps in log headers/footers should be human-readable (`%Y-%m-%d %H:%M:%S.%f`).
- The script should be structured with small, single-responsibility helper functions: one to create/determine the log file path (handling naming collisions), one to write the log header, one to write the log footer, and a `main()` function orchestrating argument parsing, subprocess invocation, live output handling, and logging.
- The script should have a shebang line pointing to the Termux Python 3.12 binary (`#!/data/data/com.termux/files/usr/bin/python3.12`) and use `from __future__ import annotations`.
- `main()` should return/propagate an appropriate exit code, and the script should call `sys.exit(main())` (or equivalent) when run as the entry point.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/R7orKoRK9MhV5Y85agjEJf"""

from __future__ import annotations
import datetime
import os
import subprocess
import sys
from pathlib import Path

LOG_DIR = Path.home() / "tmp" / "apps"
FSA = "/data/data/com.termux/files/home/bashbin/felo-sa.mjs"


def create_log_file():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file = LOG_DIR / f"felo_{timestamp}.txt"
    counter = 1
    while log_file.exists():
        log_file = LOG_DIR / f"felo_{timestamp}_{counter}.txt"
        counter += 1
    return log_file


def write_log_header(log_file, cmd_args):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("================================\n")
        f.write(f"Started: {timestamp}\n")
        f.write(f"Working directory: {os.getcwd()}\n")
        f.write(f"Arguments: {cmd_args!r}\n")
        f.write("--- Output ---\n")


def write_log_footer(log_file, exit_code):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n--- End ---\n")
        f.write(f"Finished: {timestamp}\n")
        f.write(f"Exit code: {exit_code}\n")
        f.write("================================\n")


def main():
    log_file = create_log_file()
    cmd_args = sys.argv[1:]
    if not cmd_args:
        print("Usage: felo <query>", file=sys.stderr)
        return 2
    query = " ".join(cmd_args)
    cmd = [
        "node",
        FSA,
        "--query",
        query,
        "--accept-language",
        "en",
        "--timeout",
        "300",
    ]
    process = None
    exit_code = 1
    write_log_header(log_file, cmd_args)
    try:
        with open(log_file, "a", encoding="utf-8") as log_f:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            if process.stdout is not None:
                for line in process.stdout:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    log_f.write(line)
                    log_f.flush()
            exit_code = process.wait()
    except KeyboardInterrupt:
        exit_code = 130
        print("\nInterrupted by user", file=sys.stderr)
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait()
    except Exception as e:
        error_msg = f"Error running command: {e}\n"
        sys.stderr.write(error_msg)
        with open(log_file, "a", encoding="utf-8") as log_f:
            log_f.write(error_msg)
    finally:
        write_log_footer(log_file, exit_code)
        print(f"Log saved to: {log_file}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
