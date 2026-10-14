#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a batch-processing command-line wrapper around an external command-line tool. The script should take a file extension, the name of an external CLI application, and any additional arguments for that application from the command line. It should validate that the extension begins with a dot, then scan the current working directory (non-recursively) for all files matching that extension and run the external tool once per file, passing along the user-supplied extra arguments followed by the path of each file.
Key behaviors to implement:
- Print a clear usage message with examples and exit with a non-zero status when required arguments are missing.
- Reject an extension that does not start with a dot, printing a helpful error and exiting with a non-zero status.
- Process files in parallel using a pool of worker processes sized to the number of available CPU cores, so that many files are handled concurrently.
- For each file, report the outcome with a clear status line: a success indicator and the file name when the tool succeeds, or a failure indicator, the file name, and the tool's error output when it fails. Any unexpected exception during processing of a single file should be caught and reported without stopping the batch.
- Capture the external tool's output rather than letting it flood the console, and treat the tool's exit code as the success signal.
- If no matching files are found, inform the user and exit gracefully.
- Print a summary at the end showing how many files were processed successfully and how many failed.
- Run the main logic only when the script is executed directly.
Inputs: the file extension, the external application name, and optional pass-through arguments supplied on the command line. Outputs: per-file status messages and a final summary printed to the console, with the external tool performing the actual file transformations in place or as configured by the passed arguments.
---"""

from __future__ import annotations
from functools import partial
from multiprocessing import Pool, cpu_count
from pathlib import Path
import subprocess
import sys


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
