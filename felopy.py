#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line wrapper around an external AI agent CLI. The tool accepts a free-form natural-language request from the user, along with an optional timeout setting (defaulting to five minutes), and forwards the request to the agent for processing. It should display a clear status message showing the command being run before execution begins.
Once the agent responds, the script should scan the returned text for fenced code blocks, preferring blocks explicitly marked as Python but falling back to unlabeled blocks if none are found. It should strip surrounding whitespace from each extracted block and save the code into a dedicated output directory in the user's home folder, creating that directory if it does not exist. Each saved file should receive a unique, timestamped filename so that repeated runs never overwrite earlier results. The script should report the path of each saved file to the user and handle cases where the agent returns no code blocks or fails, providing informative error messages and appropriate exit codes. It should also gracefully handle timeouts and missing external tooling, and display any errors or diagnostic output from the agent in a readable way.
---"""

from __future__ import annotations
import argparse
from datetime import datetime
import os
import re
import subprocess
import sys

SAVE_DIR = os.path.expanduser("~/tmp/apps")


def extract_code_blocks(text: str) -> list[str]:
    pattern = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)
    blocks = pattern.findall(text)
    if not blocks:
        pattern = re.compile(r"```\s*\n(.*?)```", re.DOTALL)
        blocks = pattern.findall(text)
    return [b.strip() for b in blocks]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run felo superagent and save returned code as a Python file.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for the felo command (default: 300)",
    )
    parser.add_argument(
        "query",
        nargs="+",
        help="Query string to pass to felo superagent",
    )
    args = parser.parse_args()
    query = " ".join(args.query)
    cmd = [
        "felo",
        "superagent",
        "--timeout",
        str(args.timeout),
        "--query",
        query,
    ]
    print(f"[wrapper] Running: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + "\n" + result.stderr
    blocks = extract_code_blocks(output)
    if not blocks:
        print("[wrapper] No code blocks found in felo output.", file=sys.stderr)
        print("---- felo output ----", file=sys.stderr)
        print(output, file=sys.stderr)
        print("---------------------", file=sys.stderr)
        sys.exit(1)
    code = "\n\n".join(blocks)
    os.makedirs(SAVE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"felo_{timestamp}.py"
    filepath = os.path.join(SAVE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
    print(filepath)


if __name__ == "__main__":
    main()
