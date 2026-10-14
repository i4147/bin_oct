#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that verifies whether a given set of shared library files (.so files, as used on Linux/Android-style systems) can actually be loaded at runtime. The script should accept a file or directory path as input, recursively or non-recursively locate candidate shared library files, and for each one determine whether it is a valid, loadable binary by attempting to load it through a native dynamic-loading mechanism. For every file it checks, it should report a clear status (valid or invalid) along with a human-readable reason for any failure, such as the file not existing, not being a regular file, or the loader raising an error that describes why the library could not be loaded.
The script should be structured as a reusable verifier component that can be run standalone from the command line or imported into other tools. It should support a verbose mode that emits detailed diagnostic messages, including any non-fatal warnings the loader reports, while keeping normal output concise. Results should be summarized at the end with counts of total files checked, files that passed, and files that failed, and the script should exit with a meaningful status code reflecting whether all checks succeeded.
Logging should be written to a log file rather than cluttering the console, and console output for the user should use readable, color-friendly formatting where appropriate. The script should handle unexpected errors gracefully, never crash on a single bad file, and continue verifying the remaining files. Optionally, it should allow the user to output the results as a structured report (such as JSON) for use in automated pipelines.
---"""

from __future__ import annotations
import ctypes
from pathlib import Path
import subprocess
import sys
from dh import cprint, get_files
from loguru import logger

logger.remove()
logger.add("/data/data/com.termux/files/home/tmp/apps/soverify.log")


class CtypesVerifier:
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.platform = sys.platform

    def log(self, message: str, level: str = "DEBUG") -> None:
        if self.verbose:
            getattr(logger, level.lower())(f"[CTYPES] {message}")

    def verify_so_file(self, path: Path) -> tuple[bool, str]:
        if not path.exists():
            return (False, "File does not exist")
        if not path.is_file():
            return (False, "Not a regular file")
        try:
            ctypes.CDLL(str(path), use_errno=True)
            err = ctypes.get_errno()
            if err:
                self.log(f"Warning: errno set to {err} for {path.name}")
            return (True, "ok")
        except OSError as e:
            error_msg = f"OSError: {e}"
            self.log(f"Failed to load {path.name}: {error_msg}", "ERROR")
            return (False, error_msg)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            self.log(f"Failed to load {path.name}: {error_msg}", "ERROR")
            return (False, error_msg)

    def verify_with_symbols(self, path: Path) -> tuple[bool, dict]:
        can_load, msg = self.verify_so_file(path)
        symbol_info = {
            "can_load": can_load,
            "message": msg,
            "has_symbols": False,
            "symbol_count": 0,
        }
        if not can_load:
            return (False, symbol_info)
        try:
            result = subprocess.run(["nm", str(path)], capture_output=True, timeout=10, text=True)
            if result.returncode == 0:
                lines = [line for line in result.stdout.split("\n") if line.strip()]
                symbol_info["symbol_count"] = len(lines)
                symbol_info["has_symbols"] = len(lines) > 0
                self.log(f"Found {len(lines)} symbols in {path.name}")
        except FileNotFoundError:
            self.log(
                "'nm' command not found. Install binutils for symbol analysis",
                "WARNING",
            )
        except subprocess.TimeoutExpired:
            self.log(f"Symbol extraction timed out for {path.name}", "WARNING")
        except Exception as e:
            self.log(f"Could not extract symbols from {path.name}: {e}", "ERROR")
        return (can_load, symbol_info)


def verify_single_file(path: Path) -> bool | None:
    try:
        verifier = CtypesVerifier()
        success, message = verifier.verify_so_file(path)
        if success:
            logger.debug(f"✓ {path.name}: Valid")
            return True
        else:
            logger.error(f"✗ {path.name}: {message}")
            cprint(f"  ✗ {path}: {message}", "red")
            return False
    except Exception as e:
        logger.error(f"✗ {path.name}: Unexpected error - {e}")
        cprint(f"  ✗ {path}: Unexpected error - {e}", "red")
        return False


def collect_files(args: list[str]) -> list[Path]:
    if not args:
        return get_files(Path.cwd(), ext=[".so"])
    files = []
    for arg in args:
        path = Path(arg)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(get_files(path, ext=[".so"]))
        else:
            cprint(f"Warning: {path} does not exist", "yellow")
    return files


def main() -> None:
    files = collect_files(sys.argv[1:])
    if not files:
        cprint("No .so files found to verify", "yellow")
        return
    print(f"\nVerifying {len(files)} shared object file(s)...\n")
    valid_count = 0
    error_count = 0
    error_files = []
    for path in files:
        result = verify_single_file(path)
        if result is True:
            valid_count += 1
        elif result is False:
            error_count += 1
            error_files.append(path)
    print(f"\n{'=' * 40}")
    print("VERIFICATION SUMMARY")
    print(f"{'=' * 40}")
    print(f"Total files checked: {len(files)}")
    print(f"✓ Valid files:       {valid_count}")
    print(f"✗ Files with errors: {error_count}")
    if error_files:
        print(f"\n{'=' * 40}")
        print("FILES WITH ERRORS:")
        print(f"{'=' * 40}")
        for path in error_files:
            print(f"  ✗ {path}")
    print(f"Verification complete: {valid_count} valid, {error_count} errors out of {len(files)} files")
    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    gil_state = ctypes.pythonapi.PyGILState_Ensure()
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        cprint("\nVerification interrupted by user", "yellow")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        cprint(f"Fatal error: {e}", "red")
        sys.exit(1)
    finally:
        ctypes.pythonapi.PyGILState_Release(gil_state)
    Path("/sdcard/soverify.log").unlink()
