#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line tool for recovering the password of a password-protected ZIP archive using a wordlist-based dictionary attack. The tool should take the path to the ZIP file and a path to a text file containing candidate passwords (one per line) as inputs, and should attempt each candidate against the archive until it finds the correct password or exhausts the list.
The script should leverage multiple CPU cores to speed up the search, dividing the candidate passwords into batches that are distributed across parallel worker processes. The batch size and the interval for progress updates should be configurable from the command line, with sensible defaults. Each worker should validate candidates against the archive without extracting any files to disk.
While running, the tool should periodically report progress to the user, including the number of passwords tested, the current rate of attempts per second, and the elapsed time, formatted in a human-readable way (for example, hours, minutes, and seconds as appropriate). Once the search completes, it should clearly report whether the password was found, and if so, display the recovered password, along with a summary of the total attempts made and the total time taken.
The tool should handle common error conditions gracefully with clear user-facing messages, such as a missing or unreadable archive file, a missing or empty wordlist, an archive that is not password-protected, or an invalid command-line argument. It should stop all worker processes cleanly when a password is found or when the user interrupts execution (for example with Ctrl+C), and it should exit with appropriate status codes indicating success, failure to find the password, or error. The script should be designed for use on the command line, with help text describing its usage and options.
---"""

from __future__ import annotations
import argparse
from dataclasses import dataclass, field
from itertools import islice
import multiprocessing
from pathlib import Path
import sys
import time
from typing import TYPE_CHECKING, Final
import zipfile

if TYPE_CHECKING:
    from collections.abc import Generator
DEFAULT_BATCH_SIZE: Final[int] = 2000
DEFAULT_UPDATE_INTERVAL: Final[float] = 5.0


@dataclass
class CrackResult:
    success: bool = False
    password: str | None = None
    tested_count: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None

    @property
    def elapsed(self) -> float:
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def pps(self) -> float:
        return self.tested_count / self.elapsed if self.elapsed > 0 else 0.0


def format_duration(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def check_password_batch(zip_path: Path, passwords: list[str]) -> tuple[str | None, int]:
    tested = 0
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for pwd in passwords:
                tested += 1
                try:
                    first_file = zf.filelist[0].filename
                    with zf.open(first_file, pwd=pwd.encode()) as f:
                        f.read(1)
                    return (pwd, tested)
                except (RuntimeError, zipfile.BadZipFile, zf.error):
                    continue
    except Exception:
        pass
    return (None, tested)


def get_wordlist_batches(path: Path, batch_size: int) -> Generator[list[str], None, None]:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        while True:
            batch = [line.strip() for line in islice(f, batch_size) if line.strip()]
            if not batch:
                break
            yield batch


def count_lines(path: Path) -> int:
    count = 0
    with path.open("rb") as f:
        for _line in f:
            count += 1
    return count


def brute_force_zip(
    zip_path: Path,
    wordlist_path: Path,
    num_processes: int | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    update_interval: float = DEFAULT_UPDATE_INTERVAL,
) -> CrackResult:
    if not zip_path.exists():
        print(f"❌ Error: Zip file not found: {zip_path}")
        return CrackResult()
    if not wordlist_path.exists():
        print(f"❌ Error: Wordlist not found: {wordlist_path}")
        return CrackResult()
    try:
        with zipfile.ZipFile(zip_path) as zf:
            if not any(info.flag_bits & 1 for info in zf.infolist()):
                print("⚠️  Warning: Zip file does not appear to be password protected.")
    except zipfile.BadZipFile:
        print("❌ Error: Invalid zip file.")
        return CrackResult()
    num_processes = num_processes or multiprocessing.cpu_count()
    print(f"🔍 Counting passwords in {wordlist_path.name}...")
    total_passwords = count_lines(wordlist_path)
    print(f"📊 Total passwords to test: {total_passwords:,}")
    print(f"🚀 Starting attack with {num_processes} processes...")
    print(f"{'=' * 40}")
    result = CrackResult(start_time=time.time())
    last_update = result.start_time
    try:
        with multiprocessing.Pool(processes=num_processes) as pool:
            batches = get_wordlist_batches(wordlist_path, batch_size)
            worker_args = ((zip_path, batch) for batch in batches)
            for found_pwd, tested_in_batch in pool.starmap(check_password_batch, worker_args):
                result.tested_count += tested_in_batch
                current_time = time.time()
                if found_pwd:
                    result.success = True
                    result.password = found_pwd
                    result.end_time = current_time
                    pool.terminate()
                    break
                if current_time - last_update >= update_interval:
                    progress = result.tested_count / total_passwords * 40 if total_passwords > 0 else 0
                    elapsed = current_time - result.start_time
                    pps = result.tested_count / elapsed if elapsed > 0 else 0
                    print(
                        f"Progress: {progress:6.2f}% | Tested: {result.tested_count:10,} | Speed: {
                            pps:8.1f} p/s | Elapsed: {format_duration(elapsed)}",
                        end="\r",
                    )
                    last_update = current_time
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
        result.end_time = time.time()
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        result.end_time = time.time()
    finally:
        if not result.end_time:
            result.end_time = time.time()
    print("\n" + "=" * 40)
    if result.success:
        print(f"✅ SUCCESS! Password found: {result.password}")
    else:
        print("❌ FAILED. Password not found in wordlist.")
    print(f"⏱️  Total time: {format_duration(result.elapsed)}")
    print(f"🔢 Total tested: {result.tested_count:,}")
    print(f"⚡ Average speed: {result.pps:.1f} passwords/second")
    print("-" * 40)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Optimized Zip Brute-Forcer for Python 3.12",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("zip_file", type=Path, help="Path to the protected zip file")
    parser.add_argument(
        "-w",
        "--wordlist",
        type=Path,
        default=Path("wordlist.txt"),
        help="Path to the password wordlist",
    )
    parser.add_argument(
        "-p",
        "--processes",
        type=int,
        help="Number of parallel processes (default: CPU count)",
    )
    parser.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Passwords per worker batch",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=DEFAULT_UPDATE_INTERVAL,
        help="Status update interval in seconds",
    )
    args = parser.parse_args()
    try:
        result = brute_force_zip(
            args.zip_file,
            args.wordlist,
            num_processes=args.processes,
            batch_size=args.batch_size,
            update_interval=args.interval,
        )
        sys.exit(0 if result.success else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
