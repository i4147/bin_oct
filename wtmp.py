#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that watches a user-specified directory tree for newly created package and archive files and automatically copies matching files into a fixed collection folder in the user's home directory (created if it does not exist).
Requirements:
- Purpose: Continuously monitor a given folder (and its subfolders) so that any archive or distribution package file appearing there is mirrored into a central staging location, preserving the original file name and metadata such as timestamps.
- Supported file types: only files whose names end with one of these suffixes: `.tar.gz`, `.whl`, `.tar.xz`, `.zip`, `.tar.bz2`. Multi-part suffixes must be matched correctly; all other files must be ignored.
- Startup behavior: when launched, the script should first scan the entire target finds, before switching to live monitoring.
- Live behavior: after the initial scan, the script should react to newly created files in the watched tree (including those inside newly created subdirectories) and copy matching ones immediately. Directories themselves must not be copied.
- Output: print the full source path of each file successfully copied. If a copy fails, print a clear error message that includes the file path and the reason, and keep the script running.
- Input: the watched directory should be accepted as a command-line argument; the script should run until interrupted by the user (e.g., Ctrl+C), then shut down cleanly.
- Destination: create the staging folder automatically (including parent directories) if it is missing, and handle the case where the same file name already exists there by overwriting it.
- Robustness: the script must not crash on transient errors such as permission problems or files removed mid-copy.
- Use a cross-platform approach so it works on Linux, macOS, and Windows, with the home directory resolved correctly on each system.
- Keep the implementation simple, self-contained, and readable, with brief comments explaining the main behavior.
---"""

from __future__ import annotations
import os
import pathlib
import shutil
import sys
import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

DEST_DIR = pathlib.Path("~/tmp/tgz").expanduser()
ALLOWED_EXTENSIONS = (
    ".tar.gz",
    ".whl",
    ".tar.xz",
    ".zip",
    ".tar.bz2",
)


def copy_if_match(src_path) -> None:
    if src_path.endswith(ALLOWED_EXTENSIONS):
        try:
            pathlib.Path(DEST_DIR).mkdir(exist_ok=True, parents=True)
            dest = os.path.join(
                DEST_DIR,
                pathlib.Path(src_path).name,
            )
            shutil.copy2(src_path, dest)
            print(src_path)
        except Exception as e:
            print(f"Failed to copy {src_path}: {e}")


def startup_scan(fpath: str) -> None:
    for root, _dirs, files in os.walk(fpath):
        for f in files:
            full_path = os.path.join(root, f)
            copy_if_match(full_path)


class CopyEventHandler(FileSystemEventHandler):
    def on_created(self, event) -> None:
        if not event.is_directory:
            copy_if_match(event.src_path)

    def on_modified(self, event) -> None:
        if not event.is_directory:
            copy_if_match(event.src_path)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/data/data/com.termux/files/usr/tmp"
    startup_scan(path)
    event_handler = CopyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
