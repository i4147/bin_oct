#!/data/data/com.termux/files/usr/bin/python3.12
"""
Python equivalent of:

    for f in *.whl; do
        unzip $f
        rm -v $f
    done

Behavior:
    * Iterate over every .whl file (a .whl is just a ZIP archive)
      in the target directory.
    * Extract each archive into the same directory that contains it.
    * Delete the original .whl **only if extraction succeeded**.
    * Any error is logged via `loguru` and the original .whl is preserved.
"""

from pathlib import Path
from zipfile import BadZipFile, ZipFile

from loguru import logger


def process_wheels(directory: Path = Path(".")) -> None:

    wheel_files = list(directory.glob("*.whl"))

    if not wheel_files:
        logger.warning("No .whl files found in {}", directory.resolve())
        return

    logger.info("Found {} .whl file(s) in {}", len(wheel_files), directory.resolve())

    for wheel_path in wheel_files:
        if not wheel_path.is_file():
            logger.debug("Skipping non-file entry: {}", wheel_path)
            continue

        logger.info("Processing {}", wheel_path.name)

        try:
            with ZipFile(wheel_path, "r") as archive:
                archive.extractall(path=wheel_path.parent)

            wheel_path.unlink()
            logger.success("Extracted and removed {}", wheel_path.name)

        except BadZipFile:
            logger.exception("{} is not a valid ZIP/wheel file; original kept", wheel_path)

        except PermissionError:
            logger.exception("Permission error on {}; original kept", wheel_path)

        except OSError:
            logger.exception("OS error while processing {}; original kept", wheel_path)

        except Exception:
            logger.exception("Unexpected error on {}; original kept", wheel_path)

    logger.info("Done.")


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    process_wheels(target)
