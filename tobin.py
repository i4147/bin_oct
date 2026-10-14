#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path from the command line and moves it into a fixed "sbin" directory located in the current user's home folder, creating that destination directory if it does not already exist. Before moving, the script must check whether a file with the same name already exists at the destination. If it does, the script should report that the target exists, compare the contents of the existing destination file and the source file using a cryptographic hash computed in streamed chunks so that large files are handled efficiently. If the contents are identical, the script should report that the hashes match, delete the source file, and exit with a non-zero status code to signal that nothing new was installed. If the contents differ, the script should overwrite or otherwise place the source file at the destination so that the source file ends up in the destination directory under its original name. When the move succeeds without any conflict, the script should complete silently or with minimal output and exit successfully. The script should handle the case where no command-line argument is provided by displaying a clear usage message, and it should treat missing source files and permission problems gracefully with informative error messages rather than unhandled tracebacks. The overall behavior should be simple, reliable, and suitable for use as a command-line utility that installs or deduplicates executable scripts into a personal bin directory.
---"""

from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import sys

CHUNK_SIZE = 32768
dest = Path.home() / "sbin"


def get_sha256(path: str | Path) -> str:
    path = Path(path)
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    fn = Path(sys.argv[1])
    dest_path = dest / fn.name
    if dest_path.exists():
        print("target exists")
        if get_sha256(dest_path) == get_sha256(fn):
            print("the target hash and source are equal")
            fn.unlink()
            sys.exit(1)
    fn.rename(dest_path)


if __name__ == "__main__":
    raise SystemExit(main())
