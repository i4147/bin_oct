#!/usr/bin/env python3
"""upkl.py — unpack a pickle of raw bytes into a sibling ``.raw`` file.

Only built-in containers and scalars are accepted. Global names are refused by a
restricted unpickler, so a hostile pickle cannot execute code on load — the
original called ``pickle.load`` directly, which could.
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from reqs.atomicio import atomic_write

__version__ = "1.0.0"


class _RestrictedUnpickler(pickle.Unpickler):
    """Refuse every global lookup so loading a pickle cannot import code."""

    def find_class(self, module: str, name: str) -> Any:
        """Reject any attempt to resolve a global name."""
        raise pickle.UnpicklingError(f"refusing to load global {module}.{name}")


class PickleUnpacker:
    """Write the payload of a bytes pickle next to the pickle itself."""

    def __init__(self, path: Path, *, dry_run: bool = False) -> None:
        """Store the pickle path and whether to skip the write."""
        self._path = path
        self._dry_run = dry_run

    def load(self) -> bytes:
        """Return the bytes stored in the pickle."""
        with self._path.open("rb") as handle:
            data = _RestrictedUnpickler(handle).load()
        if not isinstance(data, bytes):
            raise pickle.UnpicklingError(f"expected bytes, found {type(data).__name__}")
        return data

    def run(self) -> int:
        """Unpack the pickle and return a process exit code."""
        data = self.load()
        target = self._path.with_suffix(".raw")
        if self._dry_run:
            print(f"would write {len(data)} bytes to {target}")
            return 0
        atomic_write(target, data)
        print(data)
        return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for ``upkl.py``."""
    parser = argparse.ArgumentParser(
        prog="upkl.py",
        description="Unpack a pickled bytes object into a .raw file.",
    )
    parser.add_argument("path", type=Path, help="pickle file to unpack")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and unpack the pickle."""
    args = _build_parser().parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    try:
        return PickleUnpacker(args.path, dry_run=args.dry_run).run()
    except (OSError, pickle.UnpicklingError, EOFError) as exc:
        logger.error("cannot unpack {}: {}", args.path, exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
