#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to recreate a Python script with the following specification:

Create a single-file Python 3 command-line script intended for Termux on Android (use the shebang `#!/data/data/com.termux/files/usr/bin/env python`). The script recursively compiles C and C++ source files found under the current working directory, in parallel, and reports the results.

Requirements:

**Imports and dependencies**
- Use only the Python standard library: `from __future__ import annotations`, `subprocess`, `sys`, `multiprocessing.Pool`, and `pathlib.Path`.

**Top-level worker function (must be a module-level function so it can be pickled by multiprocessing)**
- Name it `compile_file` and have it accept a single tuple argument containing: the source file path (a `Path`), the compiler command name (a string), and the desired output path (a `Path`).
- Build the command as: compiler, then the source path as a string, then `-o`, then the output path as a string.
- Run it with `subprocess.run`, capturing stdout and stderr as text, with a 60-second timeout.
- On return code 0, return a tuple of (source path as string, `True`, and a success message of the form "✓ Compiled: <source file name> -> <output file name>").
- On a non-zero return code, return (source path as string, `False`, and a failure message of the form "✗ Failed: <source file name>" followed by a newline and the captured stderr).
- Catch `subprocess.TimeoutExpired` and return a failure tuple with the message "✗ Timeout: <source file name>".
- Catch any other `Exception` and return a failure tuple with the message "✗ Error: <source file name> - <exception text>".
- Every path returns the same 3-element tuple shape: (path string, success boolean, message string).

**`main` function**
- Set the root directory to the current working directory (`Path.cwd()`).
- Print "Scanning directory: <root path>" followed by a blank line.
- Collect all `*.c` files and all `*.cpp` files recursively using `rglob`, into separate lists.
- Build a task list: for each `.c` file, the task is (file, "clang", file with its suffix removed); for each `.cpp` file, the task is (file, "clang++", file with its suffix removed). Process all C tasks before C++ tasks.
- If there are no tasks, print a message saying no `.c` or `.cpp` files were found, and exit with a nonzero status code via `sys.exit`.
- Otherwise, compile all tasks in parallel using a `multiprocessing.Pool` (default worker count), via `imap`/`map`-style iteration over the task list.
- For each result, print its message. Track the count of successes and failures.
- After completion, print a summary line showing the number of successful and failed compilations (for example, "Done: X succeeded, Y failed"), and exit with status 1 if any failed, otherwise exit normally (status 0).

**Entry point**
- Guard the call to `main()` with the standard `if __name__ == "__main__":` check. Use `multiprocessing` safe conventions so it works when spawning workers.

**Behavior notes and edge cases**
- Output names are the source path with its extension removed, in the same directory as the source file; existing output files will be overwritten by the compiler.
- Files are discovered recursively, so nested directories are included.
- Compiler availability is not checked up front; a missing compiler surfaces as a per-file "Error" message rather than crashing the script.
- Stderr is included in the output only for failed compilations.
- Output should be written to stdout using the exact symbols (✓ and ✗) and formatting described above.
- Keep the code concise, idiomatic, with minimal comments and no external dependencies.
---"""

from __future__ import annotations

import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path


def compile_file(args):
    path, compiler, output_path = args
    try:
        cmd = [compiler, str(path), "-o", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return (
                str(path),
                True,
                f"✓ Compiled: {path.name} -> {output_path.name}",
            )
        else:
            return (
                str(path),
                False,
                f"✗ Failed: {path.name}\n{result.stderr}",
            )
    except subprocess.TimeoutExpired:
        return (str(path), False, f"✗ Timeout: {path.name}")
    except Exception as e:
        return (str(path), False, f"✗ Error: {path.name} - {e!s}")


def main():
    root_dir = Path.cwd()
    print(f"Scanning directory: {root_dir}\n")
    c_files = list(root_dir.rglob("*.c"))
    cpp_files = list(root_dir.rglob("*.cpp"))
    tasks = []
    for c_file in c_files:
        output_path = c_file.with_suffix("")
        tasks.append((c_file, "clang", output_path))
    for cpp_file in cpp_files:
        output_path = cpp_file.with_suffix("")
        tasks.append((cpp_file, "clang++", output_path))
    if not tasks:
        print("No .c or .cpp files found.")
        return
    print(f"Found {len(c_files)} .c file(s) and {len(cpp_files)} .cpp file(s)")
    print(f"Starting compilation with 4 workers...\n")
    with Pool(processes=4) as pool:
        results = pool.map(compile_file, tasks)
    print("\n" + "=" * 40)
    print("Compilation Results:")
    print("=" * 40 + "\n")
    successful = 0
    failed = 0
    for _path, success, message in results:
        print(message)
        if success:
            successful += 1
        else:
            failed += 1
    print("\n" + "=" * 40)
    print(f"Summary: {successful} successful, {failed} failed")
    print("=" * 40)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    raise SystemExit(main())
