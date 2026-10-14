#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that exports the list of packages installed on a Debian-based system into a structured tabular file. The script should query the system's package manager for all installed packages and collect, for each package, a fixed set of metadata fields: package name, version, architecture, installation status, priority, section, installed size, maintainer, homepage, short description, source package, essential flag, multi-arch setting, origin, and bug-tracker URL. It should produce two output files in a designated backup directory on the device: one tab-separated file and one comma-separated file, both containing a header row followed by one row per installed package, with the same data in each. The script should create the output directory if it does not exist, handle the case where the package query tool is unavailable (reporting that the system is not Debian-based and exiting cleanly), and surface any errors from the package query in a clear, user-friendly message before exiting. Upon success, it should print a concise confirmation to the user indicating where the files were written and how many packages were exported. Prioritize robustness with descain tabs, commas, quotes, or newlines so that the output files remain valid and parseable.
---"""

from __future__ import annotations
import csv
from pathlib import Path
import subprocess
import sys

OUTPUT_DIR = Path("/sdcard/backups")
TSV_FILE = OUTPUT_DIR / "installed.tsv"
CSV_FILE = OUTPUT_DIR / "installed.csv"
FIELDS = [
    "Package",
    "Version",
    "Architecture",
    "Status",
    "Priority",
    "Section",
    "Installed-Size",
    "Maintainer",
    "Homepage",
    "Description",
    "Source",
    "Essential",
    "Multi-Arch",
    "Origin",
    "Bugs",
]
FORMAT = """${binary:Package}	${Version}	${Architecture}	${Status}	${Priority}	${Section}	${Installed-Size}	${Maintainer}	${Homepage}	${binary:Summary}	${Source}	${Essential}	${Multi-Arch}	${Origin}	${Bugs}
"""


def query_packages() -> list[list[str]]:
    try:
        proc = subprocess.run(
            ["dpkg-query", "-W", f"-f={FORMAT}"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        sys.exit("dpkg-query not found (not a Debian-based system)")
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.stderr.strip())
    rows = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) != len(FIELDS):
            continue
        print(cols)
        rows.append(cols)
    rows.sort(key=lambda r: int(r[6] or 0), reverse=True)
    return rows


def save_tsv(rows: list[list[str]]) -> None:
    with TSV_FILE.open("w", encoding="utf-8") as f:
        f.write("\t".join(FIELDS) + "\n")
        for row in rows:
            f.write("\t".join(row) + "\n")


def save_csv(rows: list[list[str]]) -> None:
    with CSV_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        writer.writerows(rows)


def main() -> None:
    rows = query_packages()
    save_tsv(rows)
    save_csv(rows)
    print(f"Saved {len(rows)} packages")
    print(f"TSV: {TSV_FILE}")
    print(f"CSV: {CSV_FILE}")


if __name__ == "__main__":
    raise SystemExit(main())
