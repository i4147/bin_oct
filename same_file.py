#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python function that determines whether two given file paths refer to the same underlying file on disk, using pathlib's Path.samefile method for the comparison.
The function should accept two string path arguments and return a boolean result.
If either path does not exist, it should catch the FileNotFoundError and return False instead of raising an exception.
For any other OSError encountered during the check, it should print an error message to stderr (prefixed with "error:") and also return False."""

from __future__ import annotations

import sys
from pathlib import Path


def samefile(path1: str, path2: str) -> bool:
    try:
        return Path(path1).samefile(path2)
    except FileNotFoundError:
        return False
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return False
