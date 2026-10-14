#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a logging wrapper around an external Node.js command-line tool. The script should accept arbitrary command-line arguments from the user, forward them to the external tool, and capture everything the tool produces into a uniquely named log file for later review.
Key requirements:
- **Purpose:** Run a separately installed script-based CLI tool (located at a fixed path in a Termux-style Android environment) with the same arguments the user supplied to the wrapper, while recording a complete transcript of the run.
- **Inputs:** Command-line arguments passed to the wrapper, which are forwarded unchanged to the underlying tool. The wrapper should also work when invoked with no arguments.
- **Outputs:** A log directory in the user's home area (created automatically if missing) containing one text file per run. Each log file should be named with a timestamp at microsecond precision and must never overwrite an existing file; if a name collision occurs, append an incrementing suffix.
- **Log contents:** Each log should begin with a clear header block showing the start time, the working directory at invocation, and the exact arguments passed, followed by a visible section marker for the tool's output. After the run, a matching footer should record the end time and the tool's exit code.
- **Behavior:** The wrapper should stream the tool's standard output and standard error to the user's terminal in real time while also writing them to the log file. It should preserve the tool's exit code so that the wrapper itself exits with the same status, enabling use in shell pipelines and scripts.
- **Error handling:** If the log directory cannot be created or the log file cannot be written, the wrapper should report a clear message to the user rather than failing silently. If the underlying tool is missing or cannot be launched, the failure should be recorded and reported with a non-zero exit status.
- **Encoding:** All log text should be written using UTF-8.
- **Style:** Keep the script self-contained, readable, and runnable directly from the command line with no required third-party dependencies.
---"""

from __future__ import annotations
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys

LOG_DIR = Path.home() / "tmp" / "apps"
FSA = "/data/data/com.termux/files/home/bashbin/felo-sa.mjs"


def create_log_file():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file = LOG_DIR / f"felo_{timestamp}.txt"
    counter = 1
    while log_file.exists():
        log_file = LOG_DIR / f"felo_{timestamp}_{counter}.txt"
        counter += 1
    return log_file


def write_log_header(log_file, cmd_args):
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("================================\n")
        f.write(f"Started: {timestamp}\n")
        f.write(f"Working directory: {os.getcwd()}\n")
        f.write(f"Arguments: {cmd_args!r}\n")
        f.write("--- Output ---\n")


def write_log_footer(log_file, exit_code):
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
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
