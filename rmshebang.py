#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that processes Python source files in parallel to strip a leading shebang line from each file. The tool should accept an optional list of file paths from the command line; if none are provided, it should automatically discover all Python files in the current working directory. For each target file, if its first line begins with a shebang marker (such as "#!/usr/bin/env python"), remove that line and save the file with the remaining content, using UTF-8 encoding. Files without a shebang line, empty files, and files that cannot be read or written should be left untouched without crashing the overall run. Report each file that was modified by printing its name, and keep the script resilient so that a failure in one file never stops processing of the others. Processing should be distributed across a pool of worker processes using a bounded submission queue so that memory use stays limited when there are many files. The script should also measure and report the total size of the working directory before and after processing, so the user can see how much space the changes saved or affected.
---"""

from __future__ import annotations
from collections import deque
from multiprocessing import get_context
from pathlib import Path
import sys
from dh import fsz, get_files, gsz

MAX_QUEUE = 16


def process_file(path) -> None:
    path = Path(path)
    try:
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        new_lines = []
        if lines[0].startswith("#!/"):
            new_lines = lines[1:]
            content = "\n".join(new_lines)
            path.write_text(content, encoding="utf-8")
            print(f"{path.name} updated.")
            return
        return
    except Exception:
        pass


def main() -> None:
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    files = [Path(arg) for arg in args] if args else get_files(cwd, ext=[".py"])
    with get_context("spawn").Pool(8) as pool:
        pending = deque()
        for f in files:
            pending.append(pool.apply_async(process_file, (f,)))
            if len(pending) > MAX_QUEUE:
                pending.popleft().get()
        while pending:
            pending.popleft().get()
    diffsize = before - gsz(cwd)
    print(f"space saved: {fsz(diffsize)}")


if __name__ == "__main__":
    raise SystemExit(main())
