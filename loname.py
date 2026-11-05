#!/data/data/com.termux/files/usr/bin/env python

import re
import string
import sys
from pathlib import Path

from dh import unique_path

recursive = "-r" in sys.argv


_CYAN: str = "\033[36m"
_RESET: str = "\033[0m"

_PUNCT_TO_REMOVE: str = string.punctuation.replace("_", "").replace("-", "").replace(":", "")
_TRANSLATE_TABLE = str.maketrans({c: None for c in _PUNCT_TO_REMOVE} | {" ": "_"})
_COLLAPSE_RE = re.compile(r"[_:\-]+")


def process_file(path: Path) -> None:
    stem = path.stem
    suffix = path.suffix
    stem = stem.lower()
    stem = stem.translate(_TRANSLATE_TABLE)
    stem = _COLLAPSE_RE.sub("_", stem)
    stem = stem.strip("/")
    if not stem:
        stem = "unnamed"
    nn = stem + suffix.lower()
    if nn == path.name:
        return
    new_path = path.with_name(nn)
    if new_path.exists():
        new_path = unique_path(new_path)
    path.rename(new_path)


def main() -> None:
    cwd = Path.cwd()
    for path in cwd.iterdir():
        if path.is_symlink():
            continue
        process_file(path)


if __name__ == "__main__":
    raise SystemExit(main())
