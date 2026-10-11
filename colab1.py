#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python script for Google Colab that backs up the top-level contents of the first site-packages directory to a Google Drive folder. The script must:

**Purpose:** Export installed Python packages from the Colab runtime's site-packages directory to `/content/drive/MyDrive/wheels` so they can be restored or reused later.

**Environment and dependencies:**
- Runs in Google Colab. Use `google.colab.drive` to mount Google Drive at `/content/drive` before any other file operation.
- Uses only the standard library otherwise: `__future__` annotations, `shutil`, `site`, `zipfile`, and `pathlib`.
- Begin the file with a Termux-style shebang line (`#!/data/data/com.termux/files/usr/bin/env python`) and enable `from __future__ import annotations`.

**Behavior:**
1. Mount Google Drive, resolve the first entry from `site.getsitepackages()` as a `Path`, and create the output directory `MyDrive/wheels` (with parents, tolerating existing directories).
2. Define a module-level tuple of excluded name prefixes: `"setuptools"` and `"pip"`. Implement a helper `excluded(name: str) -> bool` that returns True when a name starts with any of these prefixes.
3. Iterate over the immediate children of site-packages, skipping excluded names:
   - **Files:** copy each file into the output directory with `shutil.copy2`, preserving metadata and the original filename. Increment a file counter.
   - **Directories:** create `<name>.zip` in the output directory using `zipfile.ZipFile` in write mode with `ZIP_DEFLATED` compression. Recursively walk the directory with `rglob("*")`, adding only regular files whose suffix is not `.pyc`. Store each entry with a path relative to site-packages (not the package directory itself). Increment a directory counter.
   - Other entry types (symlinks to nothing, sockets, etc.) are silently ignored.
4. Print a completion report with these exact labeled lines, aligned with the column padding shown:
   - `Export completed successfully.`
   - `Site-packages source : <path>`
   - `Output directory     : <path>`
   - `Top-level files copied : <count>`
   - `Top-level dirs zipped  : <count>`
   - `Excluded packages     : torch, tensorflow`

**Notable details and edge cases:**
- The printed "Excluded packages" line lists `torch, tensorflow` as a fixed informational string, even though the actual exclusion filter only applies to `setuptools` and `pip` prefixes. Reproduce this exact mismatch as written.
- Excluding by prefix means names like `pip_something` or `setuptools-x` are also skipped.
- Zip archives are overwritten if they already exist (mode `"w"`); files are overwritten by `copy2`.
- No explicit error handling: let exceptions from mounting, copying, or zipping propagate.
- Use `print` for all output; no logging module, no return value, no command-line arguments.
- Execution is a single top-level sequence with no `main()` function or `if __name__ == "__main__"` guard.
---"""

from __future__ import annotations

import shutil
import site
import zipfile
from pathlib import Path

from google.colab import drive

drive.mount("/content/drive")
site_pkgs = Path(site.getsitepackages()[0])
out_dir = Path("/content/drive/MyDrive/wheels")
out_dir.mkdir(parents=True, exist_ok=True)
EXCLUDE_PREFIXES = "setuptools", "pip"


def excluded(name: str) -> bool:
    return name.startswith(EXCLUDE_PREFIXES)


copied_files = 0
zipped_dirs = 0
for entry in site_pkgs.iterdir():
    name = entry.name
    if excluded(name):
        continue
    if entry.is_file():
        shutil.copy2(entry, out_dir / name)
        copied_files += 1
    elif entry.is_dir():
        zip_path = out_dir / f"{name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in entry.rglob("*"):
                if path.is_file() and path.suffix != ".pyc":
                    zf.write(path, path.relative_to(site_pkgs))
        zipped_dirs += 1
print("Export completed successfully.")
print(f"Site-packages source : {site_pkgs}")
print(f"Output directory     : {out_dir}")
print(f"Top-level files copied : {copied_files}")
print(f"Top-level dirs zipped  : {zipped_dirs}")
print("Excluded packages     : torch, tensorflow")
