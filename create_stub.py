#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that generates type stub files (.pyi) for Python source files, using an external stub generator tool. The script should accept one or more Python file paths as command-line arguments; if no arguments are given, it should discover all Python files in the current working directory automatically. For each source file, it should create a corresponding stub file in the same location, but skip any file whose stub already exists, reporting that skip clearly. When generating stubs, it should report success or failure for each file, and on failure it should show the error output produced by the generator. When multiple files are provided, the script should process them concurrently or in parallel to speed up the work. After processing, it should identify which of the given files still lack a stub file and report that list to the user. The script should print concise, human-readable progress messages throughout, and exit with a success status code when handled normally, returning control cleanly after a single-file run.
---"""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys
from dh import get_files, mpf


def process_file(path) -> None:
    path = Path(path)
    print(f"processing {path.name}")
    stubfile = path.with_suffix(".pyi")
    if stubfile.exists():
        print(f"[SKIP] {path.name} (stub already exists)")
        return
    cmd = ["stubgen", str(path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[OK] {path.name}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {path.name}")
        print(f"  {e.stderr}")


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".py"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    mpf(process_file, files)
    stubless = []
    for f in files:
        stubpath = f.with_suffix(".pyi")
        if not stubpath.exists():
            stubless.append(f)
    if stubless:
        print("\nFiles without generated stubs:")
        for k in stubless:
            print(f" - {k.name}")


if __name__ == "__main__":
    raise SystemExit(main())
