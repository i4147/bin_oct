#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that repeatedly runs a user-supplied shell command until it produces an unexpected result, then reports the failure. The tool should be launched from the command line and accept the command to execute as a required positional argument.
Key requirements:
- **Input:** A shell command string provided by the user. Optionally accept a list of exit codes that are considered acceptable (defaulting to success only, i.e., code 0), and a configurable pause in seconds between iterations (defaulting to one second). Allow the user to supply a short description of the tool's purpose via help output.
- **Core behavior:** Execute the command in a loop. After each run, print a clearly labeled iteration counter so the user can track progress. If the exit code is among the allowed codes, pause for the configured interval and run again. As soon as an exit code falls outside the allowed set, stop looping immediately.
- **Output:** When the loop halts, report the iteration number at which the failure occurred and the unexpected exit code. The tool should then terminate with an appropriate process exit status reflecting the outcome.
- **Robustness:** Handle keyboard interruption gracefully, showing a clean message rather than a traceback. Validate that numeric inputs (exit codes, sleep duration) are sensible, and provide clear error messages for invalid arguments.
- **Usability:** Include built-in help documentation describing all options and their defaults. The script should be self-contained, runnable as a standalone program, and suitable for stress-testing flaky programs or reproducing intermittent failures.
---"""

from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import subprocess
import sys
import time
from typing import Optional, Sequence


def run_command(command: str, allowed_codes: tuple[int, ...], sleep: float, iteration: int) -> tuple[int, int]:
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _stdout, _stderr = process.communicate()
    print(f"Iteration {iteration}")
    if process.returncode not in allowed_codes:
        return process.returncode, iteration
    time.sleep(sleep)
    return 0, iteration


def main(args: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="run a program until it fails")
    parser.add_argument("command", type=str, help="command to run")
    parser.add_argument(
        "--code",
        dest="codes",
        default=(0,),
        nargs="+",
        type=int,
        help="allowed exit codes [DEFAULT: 0]",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        dest="sleep",
        type=float,
        default=1.0,
        help="sleep between iterations [DEFAULT: %(default)s]",
    )
    parser.add_argument(
        "-p",
        "--parallel",
        dest="parallel",
        type=int,
        default=1,
        help="number of parallel processes [DEFAULT: %(default)s]",
    )
    options = parser.parse_args(args)
    allowed_codes: tuple[int, ...] = tuple(options.codes)
    ctr: int = 0
    start_loop: float = time.time()
    try:
        if options.parallel <= 1:
            while True:
                ctr += 1
                returncode, _ = run_command(options.command, allowed_codes, options.sleep, ctr)
                if returncode != 0:
                    return returncode
        else:
            with ProcessPoolExecutor(max_workers=options.parallel) as executor:
                futures = {}
                for i in range(options.parallel):
                    ctr += 1
                    future = executor.submit(run_command, options.command, allowed_codes, options.sleep, ctr)
                    futures[future] = ctr
                while futures:
                    for future in as_completed(futures):
                        iteration = futures.pop(future)
                        returncode, _ = future.result()
                        if returncode != 0:
                            for pending in futures:
                                pending.cancel()
                            return returncode
                        ctr += 1
                        new_future = executor.submit(run_command, options.command, allowed_codes, options.sleep, ctr)
                        futures[new_future] = ctr
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
