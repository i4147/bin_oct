#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line utch-processes files in the current directory using an external CLI tool, run in parallel via multiprocessing.
It should accept a file extension, the CLI application name, and optional extra arguments from sys.argv, validate that the extension starts with a dot, then glob all matching files in the current working directory.
For each matched file it should invoke the external tool as a subprocess (appending the file path to the given CLI args), capturing stdout/stderr, and report per-file success or failure with a checkmark or cross emoji.
It should use a process pool sized to about 75% of available CPU cores, print progress/status messages, and exit gracefully with informative usage instructions if arguments are missing or no matching files are found."""

import subprocess
import sys
from functools import partial
from multiprocessing import Pool, cpu_count
from pathlib import Path


def process_file(cli_app, cli_args, path):
    try:
        cmd = [cli_app] + cli_args + [str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f"✅ Processed: {path.name}"
        else:
            return f"❌ Failed: {path.name} - {result.stderr.strip()}"
    except Exception as e:
        return f"❌ Error processing {path.name}: {e!s}"


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_script.py <extension> <cli_app> [args...]")
        print("Example: python run_script.py .svg svgo")
        print("         python run_script.py .svg svgo -c config.json -o output/")
        sys.exit(1)
    extension = sys.argv[1]
    cli_app = sys.argv[2]
    cli_args = sys.argv[3:]
    if not extension.startswith("."):
        print(f"Error: Extension must start with '.', got '{extension}'")
        sys.exit(1)
    current_dir = Path.cwd()
    files = list(current_dir.glob(f"*{extension}"))
    if not files:
        print(f"No *{extension} files found in {current_dir}")
        sys.exit(0)
    print(f"Found {len(files)} *{extension} files in {current_dir}")
    print(f"Processing with: {cli_app} {' '.join(cli_args)}")
    print("-" * 40)
    num_processes = max(1, int(cpu_count() * 0.75))
    process_func = partial(process_file, cli_app, cli_args)
    with Pool(processes=num_processes) as pool:
        results = pool.map(process_func, files)
    print("-" * 40)
    print("\n".join(results))
    success_count = sum(1 for r in results if r.startswith("✅"))
    failure_count = len(results) - success_count
    print("-" * 40)
    print(f"Summary: {success_count} successful, {failure_count} failed")


if __name__ == "__main__":
    raise SystemExit(main())
