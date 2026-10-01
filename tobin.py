#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that takes a file path as a command-line argument and moves it into a "sbin" directory located in the user's home folder.
Before moving, if a file with the same name already exists at the destination, the script must compute and compare the SHA-256 hashes (read in 32768-byte chunks) of both the source and destination files.
If the hashes match, it should print messages indicating the target exists and the hashes are equal, delete the source file, and exit with status code 1 instead of moving it.
If the destination does not exist or the hashes differ, the script should rename/move the source file into the destination directory."""

import sys
from hashlib import sha256
from pathlib import Path

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
