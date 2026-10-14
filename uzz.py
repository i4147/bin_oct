#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a given directory (defaulting to the current working directory) for Python wheel package files (.whl) and unpacks each one in place. every wheel found, the script should extract its full contents into the same directory where the wheel resides, then delete the original wheel file once extraction succeeds. The script should log its progress clearly, including how many wheel files were found, the name of each file being processed, and a success message after each wheel is extracted and removed. If no wheel files are present, it should log a warning and exit gracefully. Any entries matching the wheel pattern that are not regular files (such as directories) should be skipped with a debug-level message. If a file is not a valid ZIP archive, the script should log an error with traceback details, leave the original file untouched, and continue processing the remaining wheels. If a file cannot be extracted or removed due to insufficient permissions, the script should log an appropriate error and move on without crashing. The overall goal is a robust, batch-oriented utility that safely converts downloaded wheel archives into their extracted contents while preserving data on any failure.
---"""

from __future__ import annotations
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from loguru import logger


def process_wheels(directory: Path = Path()) -> None:
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

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path()
    process_wheels(target)
