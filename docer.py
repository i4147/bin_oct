#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script, intended to run under Termux on Android, that moves a single file into the shared-storage folder `/sdcard/doc`.

Requirements:

- Start with a Termux-style shebang line pointing to `/data/data/com.termux/files/usr/bin/env python`.
- Use `from __future__ import annotations` for forward-compatible type hints. Use only the standard library: `sys` and `pathlib.Path`.
- Define a function `process_file` that takes a single path argument (a `Path` object) and returns nothing. Annotate the return type as `None`.
- Inside `process_file`:
  1. Read the entire file contents as bytes using the path's byte-reading method.
  2. Set the target directory to the fixed absolute location `/sdcard/doc`. If it does not exist, create it with directory creation that tolerates an existing directory (no error if it already exists). Do not create parent directories beyond that one level.
  3. Build the target file path by joining the target directory with the source file's name only (not its full path).
  4. If no file already exists at the target path, write the bytes read earlier to the target path, then delete the original source file, then print exactly `done.`.
  5. If a file already exists at the target path, do not overwrite or delete anything. Instead print a message in this exact format: `target file : <name> exists. remove it and try again`, where `<name>` is the target file's name (filename only).
- Add a main guard. When run as a script, read the first command-line argument (`sys.argv[1]`), convert it to a `Path`, and pass it to `process_file`.
- Notable behavior to preserve: the operation is a copy-then-delete move, not an atomic rename, so it works across filesystems. Files are read fully into memory, so very large files are a concern. The script performs no argument-count validation, so running it without an argument raises an index error; no custom error handling or usage message is required, though one may be added if it does not change the success or conflict output.
- Edge cases to be aware of: a missing source file raises an error from the read; a nonexistent `/sdcard/doc` is created automatically; a name collision is reported and the source is left untouched; the source's directory structure is discarded and only its filename is kept.
- Usage: run from the command line as `python <script> <path-to-file>`, for example to move a file from the current directory into the shared documents folder on the Android device.
- Keep the code minimal, idiomatic, and with no extra output beyond the messages described above.
---"""

from __future__ import annotations

import sys
from pathlib import Path


def process_file(path) -> None:
    content = path.read_bytes()
    target_dir = Path("/sdcard/doc")
    if not target_dir.exists():
        target_dir.mkdir(exist_ok=True)
    target_path = target_dir / path.name
    if not target_path.exists():
        target_path.write_bytes(content)
        path.unlink()
        print("done.")
    else:
        print(f"target file : {target_path.name} exists. remove it and try again")


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    process_file(fn)
