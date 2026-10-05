#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that verifies whether installed packages can be successfully imported.
It should use importlib.metadata.distributions() to enumerate all installed packages when no command-line arguments are given, attempting to import each one, printing a checkmark with the package name on success, and logging a debug-level traceback (via loguru, writing to /sdcard/allimport.log) on failure.
If package names are passed as command-line arguments, it should instead attempt to import only those specific packages using the same success/failure reporting logic.
The script should always exit with status code 0 regardless of import failures."""

from __future__ import annotations
import sys
import traceback
from importlib import import_module
from importlib.metadata import distributions
from loguru import logger

logger.add("/sdcard/allimport.log", diagnose=True)


def tryimport(package: str) -> bool | str:
    try:
        import_module(package)
        print(f"✓ {package}")
        return True
    except Exception:
        logger.debug(f"X {package}")
        return traceback.format_exc()


def tryallimport() -> None:
    for pkg in distributions():
        pkn = pkg.metadata["name"]
        try:
            import_module(pkn)
            print(f"✓ {pkn}")
        except Exception:
            logger.debug(f"X {pkn}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        pkgs = list(args)
        for pkg in pkgs:
            tryimport(pkg)
    else:
        tryallimport()
    sys.exit(0)
